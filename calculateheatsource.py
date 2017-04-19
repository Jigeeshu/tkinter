# -*- coding: utf-8 -*-
"""
Status on 2016-09-08

@author: Ortmann
"""

import csv
import pandas as pd 
import matplotlib
matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
from time import *

def CalculateStorage(nennleistung, vl, rl):
    global t2
    stunde = 1
    speichervolumen = 0.86 * nennleistung * stunde / (vl - rl)
    
    speicherkwh = 4.182 * (vl - rl) * speichervolumen / 3.6
   
    return speicherkwh
    

def CalculateHeatSources(demand, storage, sourceshandover):
    """
    demand: list with 8760 values in kW
    *args: any number of sources as dictionary with type, rated power, priority, minimum power, ...
    """
    #hier weiter machen, gescheit das dictionary von jigeeshu einlesen
    
    sources = [] 
    i = 0
    while i < len(sourceshandover['priority']):
        sources.append({"type" : sourceshandover['type'][i], "ratedpower" : sourceshandover['rated_power'][i], "minpower" : sourceshandover['minimum_power'][i], "efficiencyfactor" : sourceshandover['efficiency_factor'][i], "priority" : sourceshandover['priority'][i]}) #sources into list
        
        i += 1

    global t2
           
        
    numbersources = len(sources) #count sources
    sources = sorted(sources, key=lambda k: k['priority'])    #sort sources by priority
    
    
    #accumulation variables. One list element for each source
    production = []
    fuel = []
    
    #hourly lists
    load = [] #list of lists. Dimension 1: Sources, dimension 2: hours
    demandrest = [] #hourly list with not provided demand
    storageload = [] #hourly list with storage load after source calculation
    storageunload = [] #hourly list with storage load after source calculation
    storagefill = [] #hourly list with storage filling
    storageloss = [] #hourly list with storage losses
    
    
    for source in sources:
        production.append(0)
        fuel.append(0)
        load.append([])
    
    i=0
    for source in load:
        for hour in demand:
            load[i].append([])
        i += 1
        
    for hour in demand:
        demandrest.append(0)
        storageload.append(0)
        storageunload.append(0)
        storagefill.append(0)
        storageloss.append(0)
           
    
    
    #simulation of each hour
    hour = 0
    for hourdemand in demand:
    
        #calculate losses in the storage
        storageloss[hour] = storage["load"] * storage ["lossfactor"]
        storage["load"] = storage["load"] - storage["load"] * storage ["lossfactor"]
        
        loadbuffer = hourdemand        
        
        #checking each source
        i = 0
        for source in sources:
            if loadbuffer >= source["ratedpower"]: #if demand ist greater then the rated power of the source
                load[i][hour] = source["ratedpower"]    #fill load variable for this source 
                production[i] += source["ratedpower"]
                fuel[i] += source["ratedpower"] / source["efficiencyfactor"]
                loadbuffer -= source["ratedpower"]  #reduce buffer by heat production
                storageload[hour] = 0
            elif loadbuffer < source["ratedpower"] and loadbuffer >= source["minpower"]: #if demand ist between rated power and min power of the source
                load[i][hour] = loadbuffer    #fill load variable for this source
                production[i] += loadbuffer
                fuel[i] += loadbuffer / source["efficiencyfactor"] #calculate fuel consumption
                loadbuffer = 0  #reduce buffer to 0
                if storage['capacity'] > storage['load']: #if storage is not full
                    storagedemand = storage['capacity'] - storage['load']
                    maxstorageload = source['ratedpower'] - load[i][hour]
                    if storagedemand <= maxstorageload: #the storage demand can be provided by the source
                        load[i][hour] += storagedemand
                        production[i] += storagedemand
                        fuel[i] += storagedemand / source["efficiencyfactor"]
                        storage['load'] = storage['capacity']
                        storagefill[hour] = storage['load']
                        storageload[hour] += storagedemand
                    else:
                        load[i][hour] = source['ratedpower']
                        production[i] += maxstorageload
                        fuel[i] += maxstorageload / source["efficiencyfactor"]
                        storage['load'] += maxstorageload
                        storagefill[hour] = storage['load']
                        storageload[hour] += maxstorageload
#                else:
#                    storageload[hour] = 0
            else:
                load[i][hour] = 0
            
            i += 1
            
            
        if storage['load'] <= loadbuffer:
            loadbuffer -= storage['load']
            storageunload[hour] = storage['load']
            storage['load'] = 0
            storagefill[hour] = storage['load']
        else:
            storageunload[hour] = loadbuffer
            storage['load'] -= loadbuffer
            loadbuffer = 0
            storagefill[hour] = storage['load']
            
        
        if loadbuffer != 0:  
            demandrest[hour] = loadbuffer
        else:
            demandrest[hour] = 0
            
        #print(storageload[hour])
        hour += 1 

    #build dataframe
    hours = ([])
    i = 1
    for element in demand:
        hours.append(i)
        i += 1

    raw_data = {}
    raw_data['hour'] = hours
    raw_data['storageunload']= storageunload
    raw_data['storageload']= storageload
    raw_data['storagefill']= storagefill
    raw_data['storageloss']= storageloss
    raw_data['demandrest']= demandrest
    raw_data['demand']= demand

    for i in range(len(load)):
       raw_data['source'+ str(i)] = load[i]

    
    #print ('storageunload:', len(raw_data['storageunload']))
    #print ('storageload:', len(raw_data['storageload']))
    #print ('hours:', len(raw_data['hour']))
    #print ('demandrest:', len(raw_data['demandrest']))
    
    print '----------------------------'
    #df = pd.DataFrame(raw_data, columns = ['hour',  'demand rest', 'demand', 'storageunload', 'storageload', 'storagefill', 'storageloss'])
    df = pd.DataFrame.from_dict(raw_data)
    #write dataframe to cvs (for testing or rawdata-storage)
    #df.to_csv(path_or_buf='test1.csv', sep=',', na_rep='', float_format=None, columns=None, header=True, index=True, index_label=None, mode='w', encoding=None, compression=None, quoting=None, quotechar='"', line_terminator='\n', chunksize=None, tupleize_cols=False, date_format=None, doublequote=True, escapechar=None, decimal='.')
    #sort dataframe by demand value
    df = df.sort('demand', axis=0, ascending=False, inplace=False)
    
    t2 = clock()

    return df
    
   
def plotprofile(df):

    print 'plotting ...'
    
    plt.ioff()
    
    # Create the general blog and the "subplots" i.e. the bars
    f, ax1 = plt.subplots(1, figsize=(10,5))
    
    # Set the bar width
    bar_width = 1
    
    # positions of the left bar-boundaries
    bar_l = [i+1 for i in range(len(df['source0']))] 
    
    # positions of the x-axis ticks (center of the bars as bar labels)
    tick_pos = [i+(bar_width/2) for i in bar_l]

    
    colsource = [i for i in list(df.columns.values) if 'source' in i]
    colour = ['#880000','#ff6666','#ffbbbb','#FF69B4','#4B0082','#800000', '#FF4500', '#FFA500']
    c = 0

    bottom = [0]*8760
    for i in colsource:
        ax1.bar(bar_l,      
                # using the pre_score data
                df[i], 
                # set the width
                width=bar_width,
                # with pre_score on the bottom
                bottom = bottom,
                # with the label pre score
                label=i, 
                # with alpha 0.5
                alpha=1, 
                # with color
                color=colour[c],
                edgecolor=colour[c],
                linewidth = 0) 
        c = c+1
        bottom = bottom + df[i]

   
    # Create a bar plot, in position bar_1
    ax1.bar(bar_l, 
            # using the post_score data
            df['storageunload'], 
            # set the width
            width=bar_width,
            # with pre_score and mid_score on the bottom
            #bottom=[i+j+k for i,j,k in zip(df['source 1'],df['source 2'],df['source 3'])], 
            bottom= bottom,
            # with the label post score
            label='storageunload', 
            # with alpha 0.5
            alpha=1, 
            # with color
            color='#32cd32',
            edgecolor='#32cd32',
            linewidth = 0)

    bottom = bottom - df['storageload']
        
    # Create a bar plot, in position bar_1
    ax1.bar(bar_l, 
            # using the post_score data
            df['storageload'], 
            # set the width
            width=bar_width,
            # with pre_score and mid_score on the bottom
            #bottom=[i+j+k-l for i,j,k,l in zip(df['source 1'],df['source 2'],df['source 3'],df['storageload'])], 
            bottom= bottom,
            # with the label post score
            label='storageload', 
            # with alpha 0.5
            alpha=1, 
            # with color
            color='#ADFF2F',
            edgecolor='#ADFF2F',
            linewidth = 0)
       
    bottom = bottom +  df['storageunload'] + df['storageload']*2
        
    # Create a bar plot, in position bar_1
    ax1.bar(bar_l, 
            # using the post_score data
            df['demandrest'], 
            # set the width
            width=bar_width,
            # with pre_score and mid_score on the bottom
            #bottom=[i+j+k+l+m for i,j,k,l,m in zip(df['source 1'],df['source 2'],df['source 3'],df['storageunload'],df['storageload'])], 
            bottom= bottom,
            # with the label post score
            label='demand rest', 
            # with alpha 0.5
            alpha=1, 
            # with color
            color='#0000aa',
            edgecolor='#0000aa',
            linewidth = 0)
    
    # set the x ticks with names
    #plt.xticks(tick_pos, df['hour'])
    
    # Set the label and legends
    ax1.set_ylabel("load [kW]")
    ax1.set_xlabel("hours")
    plt.legend(loc='upper right')
    
    
    # Set a buffer around the edge
    plt.xlim([min(tick_pos)-bar_width, max(tick_pos)+bar_width])
    
    #plt.savefig('testpng.png', dpi=300)
    plt.show()
    plt.close(f)
    
    return f

    '''
    #tried to make a step-diagram

    
    x = []
    i = 0
    while i < 8760:
        x.append(i+1)
        i += 1

    plt.plot(x, df['source 1'], drawstyle='steps', linestyle = '-')  
    plt.plot(x, df['source 1']+df['source 2'], drawstyle='steps', linestyle = '-') 
    plt.plot(x, df['source 1']+df['source 2']+df['source 3'], drawstyle='steps', linestyle = '-') 
    plt.plot(x, df['source 1']+df['source 2']+df['source 3']+df['storageunload'], drawstyle='steps', linestyle = '-') 
    plt.fill_between(x, 0, df['source 2'])
    
    plt.savefig('test3png.png', dpi=300)
    plt.close()
    
    
t1 = clock()    
    
testdemand = ([])
with open('loadcurve.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        if row[1] == "demand":
            continue
        else:        
            testdemand.append(float(row[1]))
    

teststorage = {"capacity" : CalculateStorage(1200,85,60), "lossfactor" : 0.02, "load" : 0}
testsources = {'priority': [1, 2, 3], 'rated_power': [1200, 1000, 500], 'type': ['Heizöl Kessel', 'Heizöl Kessel', 'Heizöl Kessel'], 'efficiency_factor': [0.927, 0.927, 0.927], 'minimum_power': [500, 500, 250]}
   
dataframe =CalculateHeatSources(testdemand, teststorage, testsources)

t3 = clock()

print("Berechnung:", round((t2-t1),3), "Sekunden")
print("Grafik:", round((t3-t2),3), "Sekunden")
print("Gesamt:", round((t3-t1),3), "Sekunden")

plotprofile(dataframe)

'''

