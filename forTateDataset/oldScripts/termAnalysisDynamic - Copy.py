# -*- coding: utf-8 -*-
'''
    Create adjacency matrices and analyse terms dynamically
'''
print('Create dynamic adjacency matrices and ESOMs')
#--------------------------------------------
#run create_Info_Files.py before running this
#--------------------------------------------
import pickle, time, igraph, glob, os, somoclu, collections
import itertools, codecs, seaborn, math, pprint, random, re
from matplotlib import rc
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import interactive
from scipy.spatial import distance
from matplotlib.pyplot import cm
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import matplotlib.colors as colors
import seaborn as sns
import sklearn.cluster as clusterAlgs
#--------------------------------------------
print(time.asctime( time.localtime(time.time()) ))
t = time.time()

edgeReadPath = './data/artworks_edges/dynamic'
adjMatWritePath = './data/artworks_adjacencyMats/dynamic'
distMatWritePath = './data/artworks_distanceMats/dynamic'
potentMatWritePath = './data/artworks_potentialMats/dynamic'
gravMatWritePath = './data/artworks_gravityMats/dynamic'
umatrixWritePath = './data/artworks_UMX/dynamic'
figWritePath = './data/artworks_figs/dynamic'
greenwichFigWritePath = figWritePath+'/greenwich'
greenwichUmatrixWritePath = umatrixWritePath+'/greenwich'
gephiWritePath = './data/artworks_gephi/dynamic'
statsWritePath = './data/artworks_stats'
if not os.path.exists('./data/artworks_tmp'):
    os.makedirs('./data/artworks_tmp')
if not os.path.exists(adjMatWritePath):
    os.makedirs(adjMatWritePath)
if not os.path.exists(distMatWritePath):
    os.makedirs(distMatWritePath)
if not os.path.exists(potentMatWritePath):
    os.makedirs(potentMatWritePath)
    os.makedirs(gravMatWritePath)
if not os.path.exists(umatrixWritePath):
    os.makedirs(umatrixWritePath)
if not os.path.exists(figWritePath):
    os.makedirs(figWritePath)
if not os.path.exists(gephiWritePath):
    os.makedirs(gephiWritePath)
if not os.path.exists(greenwichFigWritePath):
    os.makedirs(greenwichFigWritePath)
if not os.path.exists(greenwichUmatrixWritePath):
    os.makedirs(greenwichUmatrixWritePath)


LVLs = ['lvl1']#,'lvl2','lvl3','lvlA'] #'lvl1','lvl2','lvl3',
heatmapFonts = [12]#,7,6,4]#12,7,6,
yearPeriods = ['1800s']#,'2000s'] 
trueYearsIni = [1800]#,1964]

termLabelDict = pickle.load(open('./data/artworks_verification_labels/WmatrixLabelDict.pck','rb'))

def recRank(mylist):#Perform the Reciprocal Rank Fusion for a list of rank values
    finscore = []
    mylist=[x+1 for x in mylist]
    for rank in mylist:
        finscore.append(1/(20+rank))
    return sum(finscore)

def toroidDistance(myarray,width,height):
    somDim2 = []
    for idx,x in enumerate(myarray[:-1]):
        newxa = myarray[idx+1:]
        for nx in newxa:
            somDim2.append(np.sqrt(min(abs(x[0] - nx[0]), width - abs(x[0] - nx[0]))**2 + min(abs(x[1] - nx[1]), height - abs(x[1]-nx[1]))**2))
    SD = np.array(somDim2)
    return distance.squareform(SD)

def toroidDistanceSingle(coords1,coords2,width,height):
    return (np.sqrt(min(abs(coords1[0] - coords2[0]), width - abs(coords1[0] - coords2[0]))**2 + min(abs(coords1[1] - coords2[1]), height - abs(coords1[1]-coords2[1]))**2))

def toroidCoordinateFinder(coorx,distx,coory,disty,w,h):
    if coorx+distx>=w:
        ncx = coorx+distx-w
    elif coorx+distx<0:
        ncx = w+coorx+distx
    else:
        ncx = coorx+distx
    if coory+disty>=h:
        ncy = coory+disty-h
    elif coory+disty<0:
        ncy = h+coory+disty
    else:
        ncy = coory+disty
    return (ncx,ncy)

for lIdx,lvl in enumerate(LVLs):
    heatMapFont = heatmapFonts[lIdx]
    for idy,years in enumerate(yearPeriods):
        files = glob.glob(edgeReadPath+'/'+years+lvl+'_*.csv')
        files.sort(key=lambda x: os.path.getmtime(x))
        try:
            edgeDict = pickle.load(open('./data/artworks_tmp/edgeDictDynamic'+years+lvl+'.pck','rb'))
        except:
            edgeDict = {'uniquePersistentTerms':[]}
            termsYears = []
            for filename in files:
                periodIdx = filename[filename.index(lvl)+5:-4]
                tmpTerms = []
                edgeDict[periodIdx] = {}
                with codecs.open(filename, 'r','utf8') as f:
                    # print(filename)
                    adjList = []
                    next(f)
                    for line in f:
                        line = line.split(',')
                        tripletuple = line[:2]
                        tmpTerms.extend(tripletuple)
                        tripletuple.append(int(line[2].strip()))
                        adjList.append(tuple(tripletuple))
                    edgeDict[periodIdx]['adjList'] = adjList
                termsYears.append(list(set(tmpTerms)))
                print('There are %s unique nodes for period %s' %(len(termsYears[-1]),periodIdx))

            repetitiveTerms = collections.Counter(list(itertools.chain.from_iterable(termsYears)))
            edgeDict['allTerms'] = list(repetitiveTerms.keys())
            edgeDict['uniquePersistentTerms'] = [x for x,v in repetitiveTerms.items() if v == len(files)]
            edgeDict['uniquePersistentTerms'].sort()
            pass

            with open(statsWritePath+'/'+years+lvl+'_unique_persistent_terms.txt','w') as f:
                for word in edgeDict['uniquePersistentTerms']:
                    f.write(word+'\n')

        statement = ('For %s in the %s there are %s unique persistent terms globally out of %s unique terms' %(lvl,years,len(edgeDict['uniquePersistentTerms']),len(edgeDict['allTerms'])))
        time.sleep(5)
        print(statement)
        
        '''set up SOM'''#--------------------------------------------------------------------
        # n_columns, n_rows = 200, 120 
        # lablshift = 1
        if lvl == 'lvl1':
          n_columns, n_rows = 20, 12
          lablshift = .2
        elif lvl == 'lvl2':
          n_columns, n_rows = 40, 24
          lablshift = .3
        elif lvl == 'lvl3':
          n_columns, n_rows = 50, 30
          lablshift = .4
        elif lvl == 'lvlA':
          n_columns, n_rows = 60, 40
          lablshift = .5
        epochs2 = 3
        som = somoclu.Somoclu(n_columns, n_rows, maptype="toroid", initialization="pca")
        savefig = True
        SOMdimensionsString = 'x'.join([str(x) for x in [n_columns,n_rows]])
        #--------------------------------------------------------------------------------
        yearList = []
        count = 0
        termPrRanks, termAuthRanks, termHubRanks, termBetweenRanks = {}, {}, {}, {}
        for filename in files:
            periodIdx = filename[filename.index(lvl)+5:-4]
            yearList.append(periodIdx)
            print(periodIdx)
            # try:
            #     gUndirected = edgeDict[periodIdx]['graph']
            # except:
            gUndirected=igraph.Graph.Full(0, directed = False)
            gUndirected.es['weight'] = 1
            '''ReRanking the nodes based on their reciprocal rank between timeslots'''
            try:
                gUndirected.add_vertices(edgeDict['topTermsByPR'])
                print('used top Terms By PageRank')
                # print(edgeDict['topTermsByPR'][:5])
            except:
                gUndirected.add_vertices(edgeDict['uniquePersistentTerms'])
                print('used alphabetically ranked terms')
                pass            
            myEdges,myWeights = [], []
            nodesWithEdges = []
            WMXtermFrequencies = {termLabelDict[" ".join(re.findall("[a-zA-Z]+", x))]['code']:0 for x in edgeDict['uniquePersistentTerms']}
            print(edgeDict['uniquePersistentTerms'])
            for x in edgeDict[periodIdx]['adjList']:
                if x[0] in edgeDict['uniquePersistentTerms'] and x[1] in edgeDict['uniquePersistentTerms']:
                    myEdges.append((x[0],x[1]))
                    myWeights.append(x[2])
                    nodesWithEdges.extend(x[:2])
                    WMXtermFrequencies[termLabelDict[" ".join(re.findall("[a-zA-Z]+", x[0]))]['code']] += x[2]
                    WMXtermFrequencies[termLabelDict[" ".join(re.findall("[a-zA-Z]+", x[1]))]['code']] += x[2]
            print('Full No of edges: %s and pruned No of edges %s' %(len(edgeDict[periodIdx]['adjList']),len(myEdges)))
            gUndirected.add_edges(myEdges)
            gUndirected.es["weight"] = myWeights
            edgeDict[periodIdx]['graph'] = gUndirected
            # missingNodes = set(nodesWithEdges).symmetric_difference(edgeDict['uniquePersistentTerms'])
            # extractedCommsLouvain = gUndirected.community_multilevel(weights = 'weight').membership
            # print('Louvain comms for %s and %s formed are %s' %(years,lvl,len(set(extractedCommsLouvain))))
            # extractedCommsInfomap = gUndirected.community_infomap(edge_weights = 'weight').membership
            # print('Infomap comms for %s and %s formed are %s' %(years,lvl,len(set(extractedCommsInfomap))))

            # gephiDict = {}
            # '''Write pairs of users to txt file for Gephi'''
            # print('writing gephi file')
            # if periodIdx == str(0):
            #     if os.path.exists(gephiWritePath+'/fullAdjacencyList_' +years+lvl+'.csv'):
            #         os.remove(gephiWritePath+'/fullAdjacencyList_' +years+lvl+'.csv')
            # with open(gephiWritePath+'/fullAdjacencyList_' +years+lvl+'.csv', 'a') as geph:
            #     if periodIdx == str(0):
            #         geph.write('Id\tSource\tTarget\tWeight\tType\tTimestamp' + '\n')
            #     for idg,edg in enumerate(myEdges):
            #         towrite = [str(count+idg)]
            #         towrite.extend(list(edg))
            #         towrite.append(str(myWeights[idg]))
            #         towrite.append('undirected')
            #         towrite.append(str(1861+int(periodIdx)))
            #         geph.write('\t'.join(towrite) + '\n')
            #     count = idg+1
            # #-------------------
                # pass

            gUndirected.vs['label'] = gUndirected.vs['name']

            nodes = gUndirected.vs['name']
            # print(nodes[:5])

            #--------------------------------------------------------------------------------
            '''Extract centrality measures'''#-----------------------------------------------
            #--------------------------------------------------------------------------------
            edgeDict[periodIdx]['term'] = {'degree':{},'pageRank':{},'maxnormPageRank':{}, 'minnormPageRank':{}, 'authority':{}, 'hub':{}, 'betweenness':{}}
            pageRank = gUndirected.pagerank(weights = 'weight', directed=False)
            authority = gUndirected.authority_score(weights = 'weight') #HITS authority score
            hub = gUndirected.hub_score(weights = 'weight')#HITS hub score
            betweenness = gUndirected.betweenness(weights = 'weight', directed = False)
            # print('extracted pagerank')
            maxPR = max(pageRank)
            maxnormPageRank = [x/maxPR for x in pageRank]
            minPR = min(pageRank)
            minnormPageRank = [x/minPR for x in pageRank]
            maxminPr = max(minnormPageRank)
            minmaxPRdiff = maxPR-minPR
            minmaxnormPageRank = [1+3*((x-minPR)/minmaxPRdiff) for x in pageRank]
            for x in nodes:
                edgeDict[periodIdx]['term']['pageRank'][x] = pageRank[nodes.index(x)]
                edgeDict[periodIdx]['term']['maxnormPageRank'][x] = maxnormPageRank[nodes.index(x)]
                edgeDict[periodIdx]['term']['minnormPageRank'][x] = minnormPageRank[nodes.index(x)]
                edgeDict[periodIdx]['term']['degree'][x] = gUndirected.degree(x)
                edgeDict[periodIdx]['term']['authority'][x] = authority[nodes.index(x)]
                edgeDict[periodIdx]['term']['hub'][x] = hub[nodes.index(x)]
                edgeDict[periodIdx]['term']['betweenness'][x] = betweenness[nodes.index(x)]
            tmpPRrank = sorted(edgeDict[periodIdx]['term']['pageRank'], key=lambda k: [edgeDict[periodIdx]['term']['pageRank'][k],edgeDict[periodIdx]['term']['degree'][k],k],reverse =True)
            for x in nodes:
                if x not in termPrRanks:
                    termPrRanks[x] = [tmpPRrank.index(x)]
                else:
                    termPrRanks[x].append(tmpPRrank.index(x))

            tmpAuthrank = sorted(edgeDict[periodIdx]['term']['authority'], key=lambda k: [edgeDict[periodIdx]['term']['authority'][k],edgeDict[periodIdx]['term']['degree'][k],k],reverse =True)
            for x in nodes:
                if x not in termAuthRanks:
                    termAuthRanks[x] = [tmpAuthrank.index(x)]
                else:
                    termAuthRanks[x].append(tmpAuthrank.index(x))

            tmpHubrank = sorted(edgeDict[periodIdx]['term']['hub'], key=lambda k: [edgeDict[periodIdx]['term']['hub'][k],edgeDict[periodIdx]['term']['degree'][k],k],reverse =True)
            for x in nodes:
                if x not in termHubRanks:
                    termHubRanks[x] = [tmpHubrank.index(x)]
                else:
                    termHubRanks[x].append(tmpHubrank.index(x))

            tmpBetweenrank = sorted(edgeDict[periodIdx]['term']['betweenness'], key=lambda k: [edgeDict[periodIdx]['term']['betweenness'][k],edgeDict[periodIdx]['term']['degree'][k],k],reverse =True)
            for x in nodes:
                if x not in termBetweenRanks:
                    termBetweenRanks[x] = [tmpBetweenrank.index(x)]
                else:
                    termBetweenRanks[x].append(tmpBetweenrank.index(x))
            # -----------------------------------------------------------------------------------------------

            # -----------------------------------------------------------------------------------------------
            # '''make WMX code histograms'''#------------------------------------------------------------------
            # #make histograms of WMX codes overall------------------------------------------------------------
            # if not os.path.exists(figWritePath+'/histograms'):
            #     os.makedirs(figWritePath+'/histograms')
            #     os.makedirs(figWritePath+'/histograms/normalized')
            # if periodIdx == '0':
            #     labelFormat = 'code' #switch terms by Wmatrix code or label?
            #     allWMXcodes = [termLabelDict[" ".join(re.findall("[a-zA-Z]+", x))][labelFormat] for x in nodes]
            #     countAllWMXcodes = collections.Counter(allWMXcodes)
            #     allWMXhistLabels = sorted(list(countAllWMXcodes.keys()))
            #     allWMXhistVals = [countAllWMXcodes[x] for x in allWMXhistLabels]
            #     fig, ax = plt.subplots()
            #     ind = np.arange(len(allWMXhistVals))
            #     ax.bar(ind,allWMXhistVals,color = 'b')
            #     ax.set_ylabel('Frequency')
            #     ax.set_ylabel('WMX codes')
            #     ax.set_xticks(ind+0.5)
            #     ax.set_xticklabels(allWMXhistLabels,rotation = 90, fontsize=heatMapFont+2)
            #     plt.title('WMX category appearance histogram (Level '+lvl+' terms)')
            #     mng = plt.get_current_fig_manager()
            #     mng.window.state('zoomed')
            #     interactive(True)
            #     plt.show()            
            #     fig.savefig(figWritePath+'/histograms/appearanceWMXcodeDistribution'+years+lvl+'.png',bbox_inches='tight')
            #     plt.close()
            #     interactive(False)

            # #make histograms of WMX codes per timeslot------------------------------------------------------
            # labelFormat = 'code' #switch terms by Wmatrix code or label?
            # allWMXhistVals = [WMXtermFrequencies[x] for x in allWMXhistLabels]
            # fig, ax = plt.subplots()
            # ind = np.arange(len(allWMXhistVals))
            # ax.bar(ind,allWMXhistVals,color = 'r')
            # ax.set_ylabel('Frequency')
            # ax.set_ylabel('WMX codes')
            # ax.set_xticks(ind+0.5)
            # ax.set_xticklabels(allWMXhistLabels,rotation = 90, fontsize=heatMapFont+2)
            # plt.title('WMX category histogram per timeslot (Level '+lvl+' terms | 5 year period prior to '+str(int(periodIdx)*5+trueYearsIni[idy])+')')
            # mng = plt.get_current_fig_manager()
            # mng.window.state('zoomed')
            # interactive(True)
            # plt.show()            
            # fig.savefig(figWritePath+'/histograms/WMXcodeDistribution'+years+lvl+'_'+periodIdx+'.png',bbox_inches='tight')
            # plt.close()
            # interactive(False)

            # #make normalized histograms of WMX codes per timeslot------------------------------------------------------
            # if not os.path.exists(figWritePath+'/histograms/normalized'):            
            #     os.makedirs(figWritePath+'/histograms/normalized')
            # labelFormat = 'code' #switch terms by Wmatrix code or label?
            # print(WMXtermFrequencies)
            # print(allWMXhistLabels)
            # allWMXhistVals = [WMXtermFrequencies[x] for x in allWMXhistLabels]
            # maxallWMXhistVals = max(allWMXhistVals)
            # allWMXhistVals = [x/maxallWMXhistVals for x in allWMXhistVals]
            # fig, ax = plt.subplots()
            # ind = np.arange(len(allWMXhistVals))
            # ax.bar(ind,allWMXhistVals,color = 'r')
            # ax.set_ylabel('Frequency')
            # ax.set_ylabel('WMX codes')
            # ax.set_xticks(ind+0.5)
            # ax.set_xticklabels(allWMXhistLabels,rotation = 90, fontsize=heatMapFont+2)
            # plt.title('WMX category histogram per timeslot (Level '+lvl+' terms | 5 year period prior to '+str(int(periodIdx)*5+trueYearsIni[idy])+')')
            # mng = plt.get_current_fig_manager()
            # mng.window.state('zoomed')
            # interactive(True)
            # plt.show()            
            # fig.savefig(figWritePath+'/histograms/normalized/WMXcodeDistribution'+years+lvl+'_'+periodIdx+'.png',bbox_inches='tight')
            # plt.close()
            # interactive(False)
            #-----------------------------------------------------------------------------------------------

            #-----------------------------------------------------------------------------------------------
            '''creating undirected adjacency mat'''#--------------------------------------------------------
            #-----------------------------------------------------------------------------------------------
            # if not os.path.exists(adjMatWritePath):
            #     os.makedirs(adjMatWritePath)

            # print('creating adjacency matrix')
            # adjMat = gUndirected.get_adjacency(attribute='weight')
            # adjMat = np.array(adjMat.data)

            # print('writing undirected adjacency matrix to file')
            # with open(adjMatWritePath+'/AdjMat'+years+lvl+'_'+periodIdx+'.txt', 'w') as d:
            #     d.write('Term\t'+'\t'.join(nodes)+'\n')
            #     for s in nodes:
            #         distLine = [str(x) for x in adjMat[nodes.index(s)].tolist()]
            #         d.write(s+'\t'+'\t'.join(distLine)+'\n')

            # with open(adjMatWritePath+'/nummedAdjMat'+years+lvl+'_'+periodIdx+'.txt', 'w') as d:
            #     d.write('Term\t'+'\t'.join([str(x) for x in range(len(nodes))])+'\n')
            #     with open(figWritePath+'/nodeIdMapping'+years+lvl+'.tsv','w') as f:
            #         for idx,s in enumerate(nodes):
            #             distLine = [str(x) for x in adjMat[nodes.index(s)].tolist()]
            #             d.write(str(idx)+'\t'+'\t'.join(distLine)+'\n')
            #             f.write(str(idx)+'\t'+s+'\n')
            #-----------------------------------------------------------------------------------------------

            #-----------------------------------------------------------------------------------------------
            '''symmetrical distance matrix extraction'''
            #-----------------------------------------------------------------------------------------------
            # print('estimate symmetrical distance matrix')
            # distMat = distance.pdist(adjMat, 'euclidean')
            # distMat = distance.squareform(distMat)

            # '''Write the symmetrical distance matrix to a file'''
            # print('writing symmetrical distance matrix to file')
            # with open(distMatWritePath+'/distMat'+years+lvl+'_'+periodIdx+'.tsv', 'w') as d:
            #     d.write('Term\t'+'\t'.join(nodes)+'\n')
            #     for s in nodes:
            #         distLine = [str(float(x)) for x in distMat[nodes.index(s)].tolist()]
            #         d.write(s+'\t'+'\t'.join(distLine)+'\n')

            # '''plotting heatmap of symmetrical distance matrix'''
            # print('plotting heatmap of symmetrical distance matrix')
            # sns.set(style="darkgrid")
            # fig, ax = plt.subplots()
            # ax = sns.heatmap(distMat, square = True)#,xticklabels=2,ax=ax)
            # # ax.set_xticks(range(0, len(nodes), 4))#, minor=False)
            # ax.xaxis.tick_top()
            # ax.set_yticklabels(list(reversed(nodes)), minor=False, fontsize = heatMapFont)
            # plt.yticks(rotation=0) 
            # ax.set_xticklabels(nodes, minor=False, fontsize = heatMapFont, rotation = 90)
            # plt.xlabel('euclidean distance matrix heatmap (Level '+lvl+' terms | 5 year period prior to '+str(int(periodIdx)*5+trueYearsIni[idy])+')')
            # mng = plt.get_current_fig_manager()
            # mng.window.state('zoomed')
            # interactive(True)
            # plt.show()
            # fig.savefig(figWritePath+'/plain euclidean distance heatmaps/plainEucl_distMatHeatmap_'+years+lvl+'_'+periodIdx+'.png',bbox_inches='tight')
            # plt.close()
            # interactive(False)
            #-----------------------------------------------------------------------------------------------

            # ------------------------------------------------------------------------------------------------------------------------
            '''SOM data extraction from here on------------------------------------------------------------------------------------'''
            # ------------------------------------------------------------------------------------------------------------------------
            # '''Extract Self Organizing Maps of undirected weighted adj mats'''#change filename depending on labeled or numbered terms
            # nummedOrNot = ''#'nummed' are the labels numbers or text (leave blank)?
            # labelFormat = 'code' #switch terms by Wmatrix code or label?
            # df = pd.read_table(adjMatWritePath+'/'+nummedOrNot+'AdjMat'+years+lvl+'_'+periodIdx+'.txt', sep="\t", header=0,index_col=0)
            # dfmax = df.max()
            # dfmax[dfmax == 0] = 1
            # df = df / dfmax
            # originallabels = df.index.tolist()
            # # print(originallabels[:5])
            # labels = originallabels # labels = [termLabelDict[nodes[x]][labelFormat] for x in originallabels] #switch terms by Wmatrix code or label?
            # som.update_data(df.values)
            # if periodIdx == yearList[0]:
            #     epochs = 10
            #     radius0 = 0
            #     scale0 = 0.1
            # else:
            #     radius0 = n_rows//5
            #     scale0 = 0.03
            #     epochs = epochs2

            # #-------clustering params---------------            
            # algorithm = clusterAlgs.AffinityPropagation()
            # clusterAlgLabel = 'AffinityPropagation'# KMeans8 , SpectralClustering,AffinityPropagation, Birch
            # #---------------------------------------
            # if savefig:
            #     if not os.path.exists(figWritePath+'/Clusters/'+clusterAlgLabel+'/SOMs/'+SOMdimensionsString+'_epochs'+str(epochs2)):
            #         os.makedirs(figWritePath+'/Clusters/'+clusterAlgLabel+'/SOMs/'+SOMdimensionsString+'_epochs'+str(epochs2))
            #     SOMfilename = figWritePath+'/Clusters/'+clusterAlgLabel+'/SOMs/'+SOMdimensionsString+'_epochs'+str(epochs2)+'/SOM_'+nummedOrNot+'AdjMat'+years+lvl+'_'+periodIdx+'.png'
            #     SOMfilenameNoLabels = figWritePath+'/Clusters/'+clusterAlgLabel+'/SOMs/'+SOMdimensionsString+'_epochs'+str(epochs2)+'/noLabelsSOM_AdjMat'+years+lvl+'_'+periodIdx+'.png'                
            #     # SOMfilenameNoBMUs = figWritePath+'/Clusters/'+clusterAlgLabel+'/SOMs/'+SOMdimensionsString+'_epochs'+str(epochs2)+'/noBMUsSOM_AdjMat'+years+lvl+'_'+periodIdx+'.png'
            # else:
            #     SOMfilename = None
            # som.train(epochs=epochs, radius0=radius0, scale0=scale0)
            # #----------------------clustering-----------
            # try:
            #     som.cluster(algorithm=algorithm)
            #     print('Clustering algorithm employed: %s' %clusterAlgLabel)
            # except:
            #     som.cluster()
            #     print('Clustering algorithm employed: K-means with 8 centroids')
            #     pass
            # #----------------------clustering-----------
            # rc('font', **{'size': 11}); figsize = (20, 20/float(n_columns/n_rows))
            # som.view_umatrix(figsize = figsize, colormap="Spectral_r", bestmatches=True, labels=labels,filename=SOMfilename)
            # plt.close()
            # som.view_umatrix(figsize = figsize, colormap="Spectral_r", bestmatches=True, filename=SOMfilenameNoLabels)
            # plt.close()
            # # som.view_umatrix(figsize = figsize, colormap="Spectral_r", filename=SOMfilenameNoBMUs)
            # # plt.close()
            # edgeDict[periodIdx]['somCoords'] = {SOMdimensionsString:som.bmus}

            # colors = []
            # for bm in som.bmus:
            #     colors.append(som.clusters[bm[1], bm[0]])
            # # areas = [200]*len(som.bmus)
            # areas = [x*70 for x in minmaxnormPageRank]
            # #-----------------------------------------------------------------------------------------------

            # #-----------------------------------------------------------------------------------------------
            # '''write clustered BMUs and create piecharts of their WMX categories'''#------------------------
            # #-----------------------------------------------------------------------------------------------
            # if not os.path.exists(figWritePath+'/Clusters/'+clusterAlgLabel+'/piecharts/'+SOMdimensionsString+'_epochs'+str(epochs2)):
            #     os.makedirs(figWritePath+'/Clusters/'+clusterAlgLabel+'/piecharts/'+SOMdimensionsString+'_epochs'+str(epochs2))
            #     os.makedirs(figWritePath+'/Clusters/'+clusterAlgLabel+'/bagsOfClusteredTerms/'+SOMdimensionsString+'_epochs'+str(epochs2))

            # edgeDict[periodIdx]['clusterDict'] = {}
            # for idx,bm in enumerate(som.bmus):
            #     clusterName = som.clusters[bm[1], bm[0]] 
            #     if clusterName in edgeDict[periodIdx]['clusterDict']:
            #         edgeDict[periodIdx]['clusterDict'][clusterName]['term'].append(nodes[idx])
            #         edgeDict[periodIdx]['clusterDict'][clusterName]['WMXcode'].append(termLabelDict[" ".join(re.findall("[a-zA-Z]+", nodes[idx]))][labelFormat])
            #     else:
            #         edgeDict[periodIdx]['clusterDict'][clusterName] = {'term':[nodes[idx]],'WMXcode':[termLabelDict[" ".join(re.findall("[a-zA-Z]+", nodes[idx]))][labelFormat]]}
            # clusterNames = list(edgeDict[periodIdx]['clusterDict'].keys())

            # #write cbags of clustered terms
            # countWMXcodes = {}
            # with open(figWritePath+'/Clusters/'+clusterAlgLabel+'/bagsOfClusteredTerms/'+SOMdimensionsString+'_epochs'+str(epochs2)+'/boct'+years+lvl+'_'+periodIdx+'.tsv','w') as f:
            #     for cN in clusterNames:
            #         f.write(str(cN)+'\t'+','.join(edgeDict[periodIdx]['clusterDict'][cN]['term'])+'\n')
            #         if len(edgeDict[periodIdx]['clusterDict'][cN]['WMXcode']) > 1:
            #             countWMXcodes[cN] = collections.Counter(edgeDict[periodIdx]['clusterDict'][cN]['WMXcode'])
            # clusterNames = sorted(list(countWMXcodes.keys()))
            # clusterNum = len(countWMXcodes)

            # #make pie charts of each cluster---------------------------------------------------------------
            # pieclmns = 10
            # if pieclmns>clusterNum:
            #     pieclmns = clusterNum
            # pierows = math.ceil(clusterNum/pieclmns)
            # possibleAxes = list(itertools.product(range(pierows),range(pieclmns)))
            # fig, axarr = plt.subplots(pierows,pieclmns)
            # axarr.shape = (pierows,pieclmns)
            # fig.suptitle('Clustered WMX category vizualization (Level '+lvl+' terms | 5 year period prior to '+str(int(periodIdx)*5+trueYearsIni[idy])+')')
            # idx=0
            # for cN in clusterNames:
            #     umxLabels = list(countWMXcodes[cN].keys())
            #     umxSizes = list(countWMXcodes[cN].values())
            #     totalumxSizes = sum(umxSizes)
            #     axarr[int(idx%math.ceil(clusterNum/pieclmns)),int(idx//math.ceil(clusterNum/pieclmns))].pie(umxSizes, labels=umxLabels, startangle=90,radius=1,autopct=lambda p:'{:.0f}'.format(p*totalumxSizes/100))#autopct='%1.1f%%', , frame=True)#radius=1/clusterNum,
            #     axarr[int(idx%math.ceil(clusterNum/pieclmns)),int(idx//math.ceil(clusterNum/pieclmns))].set_aspect('equal')                
            #     axarr[int(idx%math.ceil(clusterNum/pieclmns)),int(idx//math.ceil(clusterNum/pieclmns))].set_title('cluster %s'%cN)
            #     possibleAxes.remove((int(idx%math.ceil(clusterNum/pieclmns)),int(idx//math.ceil(clusterNum/pieclmns))))
            #     idx+=1
            # for x in possibleAxes:
            #     fig.delaxes(axarr[x])
            # mng = plt.get_current_fig_manager()
            # mng.window.state('zoomed')
            # interactive(True)
            # plt.show()            
            # fig.savefig(figWritePath+'/Clusters/'+clusterAlgLabel+'/piecharts/'+SOMdimensionsString+'_epochs'+str(epochs2)+'/pie'+years+lvl+'_'+periodIdx+'.png',bbox_inches='tight')
            # plt.close()
            # interactive(False)
            #-----------------------------------------------------------------------------------------------

            #-----------------------------------------------------------------------------------------------
            '''write and show the umatrix (umx)'''#---------------------------------------------------------
            #-----------------------------------------------------------------------------------------------
            # somUmatrix =  som.umatrix
            # print('writing umatrix to file')
            # np.savetxt(umatrixWritePath+'/umx'+years+lvl+'_'+periodIdx+'.umx',somUmatrix,delimiter='\t', newline='\n',header='% '+ '%s %s'%(n_rows,n_columns))

            # print('writing BMU coords to file')
            # with open(umatrixWritePath+'/umx'+years+lvl+'_'+periodIdx+'.bm','w') as f:
            #     with open(umatrixWritePath+'/umx'+years+lvl+'_'+periodIdx+'.names','w') as fn:
            #         f.write('% '+'%s %s\n' %(n_rows,n_columns))
            #         fn.write('% '+str(len(nodes))+'\n')
            #         for idx,coos in enumerate(som.bmus):
            #             f.write('%s %s %s\n' %(idx,coos[1],coos[0]))
            #             fn.write('%s %s %s\n' %(idx,nodes[idx],nodes[idx]))

            # print('plotting umatrix 3D surface') 
            # fig = plt.figure()
            # ax = fig.gca(projection='3d')
            # X = np.arange(0, n_columns, 1)
            # Y = np.arange(0, n_rows, 1)
            # X, Y = np.meshgrid(X, Y)
            # N=somUmatrix/somUmatrix.max()
            # surf = ax.plot_surface(X, Y, somUmatrix, facecolors=cm.jet(N),rstride=1, cstride=1)#,facecolors=cm.jet(somUmatrix) cmap=cm.coolwarm, linewidth=0, antialiased=False)
            # m = cm.ScalarMappable(cmap=cm.jet)
            # m.set_array(somUmatrix)
            # plt.colorbar(m, shrink=0.5, aspect=5)
            # plt.title('SOM umatrix 3D surface vizualization (Level '+lvl+' terms | 5 year period prior to '+str(int(periodIdx)*5+trueYearsIni[idy])+')')
            # mng = plt.get_current_fig_manager()
            # mng.window.state('zoomed')
            # interactive(True)
            # plt.show()            
            # fig.savefig(figWritePath+'/SOM Umatrices/umxSurf'+years+lvl+'_'+periodIdx+'.png',bbox_inches='tight')
            # plt.close()
            # interactive(False)

            # #-----------------------------------------------------------------------------------------------
            # '''Plotting BMU coordinates with labels'''#-----------------------------------------------------
            # #-----------------------------------------------------------------------------------------------
            # labelFormat = 'code'
            # fig, ax = plt.subplots()
            # xDimension = [x[0] for x in som.bmus]#[:10]]
            # yDimension = [x[1] for x in som.bmus]#[:10]] 
            # plt.scatter(xDimension,yDimension, c=colors, s = areas, alpha = 0.7)
            # labels = [str(colors[x])+'_'+termLabelDict[" ".join(re.findall("[a-zA-Z]+", nodes[x]))][labelFormat] for x in range(len(xDimension))]
            # doneLabs = set([''])
            # for label, x, y in zip(labels, xDimension, yDimension):
            #     lblshiftRatio = 2
            #     labFinshift = ''
            #     while labFinshift in doneLabs:
            #         potentialPositions = [(x, y+lablshift), (x+lblshiftRatio*lablshift, y), (x-lblshiftRatio*lablshift, y), (x+lblshiftRatio*lablshift, y+lblshiftRatio*lablshift), 
            #         (x-lblshiftRatio*lablshift, y+lblshiftRatio*lablshift), (x+lblshiftRatio*lablshift, y-lblshiftRatio*lablshift), (x+lblshiftRatio*lablshift, y+lblshiftRatio*lablshift),
            #         (x-lblshiftRatio*lablshift, y+lblshiftRatio*lablshift)]
            #         for pP in potentialPositions:
            #             labFinshift = pP
            #             if labFinshift not in doneLabs:
            #                 break
            #         lblshiftRatio+=1
            #     doneLabs.add(labFinshift)
            #     plt.annotate(label, xy = (x, y), xytext = labFinshift, textcoords = 'data', ha = 'center', va = 'center',bbox = dict(boxstyle = 'round,pad=0.1', fc = 'white', alpha = 0.4))
            #     lIdx+=1

            # xCc = [x[1] for x in som.centroidBMcoords]
            # yCc = [x[0] for x in som.centroidBMcoords]
            # plt.scatter(xCc,yCc, c= range(len(som.centroidBMcoords)), s= [1000]*len(som.centroidBMcoords), alpha = 0.4)

            # plt.xlim(0,n_columns)
            # plt.ylim(0,n_rows) 
            # ax.invert_yaxis() 
            # plt.title('Labeled SOM. Level '+lvl+' terms, timeslot '+periodIdx+' (5 year period prior to '+str(int(periodIdx)*5+trueYearsIni[idy])+')')
            # mng = plt.get_current_fig_manager()
            # mng.window.state('zoomed')
            # interactive(True)
            # plt.show()            
            # fig.savefig(figWritePath+'/Clusters/'+clusterAlgLabel+'/SOMs/'+SOMdimensionsString+'_epochs'+str(epochs2)+'/SOM_Wmatrix'+labelFormat+'LabeledAdjMat'+years+lvl+'_'+periodIdx+'.png',bbox_inches='tight')
            # plt.close()
            # interactive(False)
            #-----------------------------------------------------------------------------------------------

            #-----------------------------------------------------------------------------------------------
            '''SOMdistance matrix quiver plots between timeslots'''#----------------------------------------
            #-----------------------------------------------------------------------------------------------
            # if int(periodIdx)>0:
            #     # X,Y = np.meshgrid( np.arange(len(nodes)),np.arange(len(nodes)) )
                
            #     X1 = [x[0] for x in edgeDict[str(int(periodIdx)-1)]['somCoords'][SOMdimensionsString][:10]]
            #     Y1 = [x[1] for x in edgeDict[str(int(periodIdx)-1)]['somCoords'][SOMdimensionsString][:10]]
            #     X2 = [x[0] for x in edgeDict[periodIdx]['somCoords'][SOMdimensionsString][:10]]
            #     Y2 = [x[1] for x in edgeDict[periodIdx]['somCoords'][SOMdimensionsString][:10]]
            #     PRcolors = [edgeDict[periodIdx]['term']['pageRank'][x] for x in nodes[:10]]

            #     pprint.pprint([X1,Y1])
            #     pprint.pprint([X2,Y2])
                
            #     fig, ax = plt.subplots()
            #     # X,Y = np.meshgrid(X1,Y1)
            #     Q = plt.quiver(X1,Y1,X2,Y2, PRcolors, cmap=cm.seismic)#,headlength=5)#    
            #     plt.xlim(0,n_columns)
            #     plt.ylim(0,n_rows)     
            #     # ax.set_xticks(range(0, len(nodes)))#, minor=False)
            #     # ax.xaxis.tick_top()
            #     # ax.set_yticklabels(list(reversed(nodes)), minor=False, fontsize = heatMapFont) 
            # plt.yticks(rotation=0) 
            #     # ax.set_xticklabels(nodes, minor=False, fontsize = heatMapFont, rotation = 90)
            #     ax.invert_yaxis() 
            #     plt.colorbar() 
            #     plt.title('SOM movement quiver plot. Level '+lvl+' terms, timeslot '+periodIdx+' (5 year period prior to '+str(int(periodIdx)*5+trueYearsIni[idy])+')')
            #     mng = plt.get_current_fig_manager()
            #     mng.window.state('zoomed')
            #     interactive(True)
            #     plt.show()
            #     fig.savefig(figWritePath+'/SOM_distanceMatQuiver_'+years+lvl+'_'+periodIdx+'.png',bbox_inches='tight')
            #     plt.close()
            #     interactive(False)
            #-----------------------------------------------------------------------------------------------

            #------------------------------------------------------------------------------------------------------------
            '''SOM distance matrix extraction'''#-----------------------------------------------------------
            #------------------------------------------------------------------------------------------------------------
            # print('estimate SOM distance matrix')
            # distMatSOM = toroidDistance(som.bmus,n_columns,n_rows)

            # '''Write the SOM distance matrix to a file'''
            # print('writing SOM distance matrix to file')
            # with open(distMatWritePath+'/distMatSOM'+years+lvl+'_'+periodIdx+'.tsv', 'w') as d:
            #     d.write('Term\t'+'\t'.join(nodes)+'\n')
            #     for s in nodes:
            #         distLine = [str(float(x)) for x in distMatSOM[nodes.index(s)].tolist()]
            #         d.write(s+'\t'+'\t'.join(distLine)+'\n')

            # '''plotting heatmap of distance matrix using som'''
            # print('plotting heatmap of distance matrix using som')
            # if not os.path.exists(figWritePath+'/SOM euclidean distance Heatmaps'):
            #     os.makedirs(figWritePath+'/SOM euclidean distance Heatmaps')
            # sns.set(style="darkgrid")
            # fig, ax = plt.subplots()
            # ax = sns.heatmap(distMatSOM, square = True)#,xticklabels=2,ax=ax)
            # # ax.set_xticks(range(0, len(nodes), 4))#, minor=False)
            # ax.set_yticklabels(list(reversed(nodes)), minor=False, fontsize = heatMapFont)
            # plt.yticks(rotation=0) 
            # ax.xaxis.tick_top()
            # ax.set_xticklabels(nodes, minor=False, fontsize = heatMapFont, rotation = 90)
            # plt.xlabel('SOM distance matrix heatmap (Level '+lvl+' terms | 5 year period prior to '+str(int(periodIdx)*5+trueYearsIni[idy])+')')
            # mng = plt.get_current_fig_manager()
            # mng.window.state('zoomed')
            # interactive(True)
            # plt.show()
            # fig.savefig(figWritePath+'/SOM euclidean distance Heatmaps/SOM_distMatHeatmap_'+years+lvl+'_'+periodIdx+'.png')#,bbox_inches='tight')
            # plt.close()
            # interactive(False)
            # #-----------------------------------------------------------------------------------------------

            # #------------------------------------------------------------------------------------------------------------
            # '''potential and gravity extraction'''#----------------------------------------------------------------------
            # #------------------------------------------------------------------------------------------------------------
            # '''estimate the potential -(PR_userN * PR_userN+1)/distance matrix'''   
            # normMethod = 'SUM'#normalization method of distance matrix
            # if normMethod == 'MAX':
            #     PRversion = 'maxnormPageRank'
            # elif normMethod == 'SUM':
            #     PRversion = 'pageRank'
            # elif normMethod == 'MIN':
            #     PRversion = 'minnormPageRank'
            # print('estimate potential')
            # potentMat = np.zeros(distMatSOM.shape)
            # pgrMat = np.zeros(distMatSOM.shape)
            # for n in nodes:
            #     potentMat[nodes.index(n)] = edgeDict[periodIdx]['term'][PRversion][n]
            #     pgrMat[:,nodes.index(n)] = edgeDict[periodIdx]['term'][PRversion][n]
            # potentMat = np.multiply(potentMat,pgrMat)
            # PRprodArray = potentMat.reshape(-1)
            # potentMat = (-potentMat)#*1000)
            # distMatPot = distMatSOM + 1
            # distMatPot = distMatPot/distMatPot.sum()#make sure this complies with the normMethod
            # potentMat = np.divide(potentMat,distMatPot)#e-8)
            # potentMat = np.multiply(potentMat,abs(np.identity(potentMat.shape[0])-1))

            # '''estimate the gravity G*(PR_userN * PR_userN+1)/distance^2 matrix'''
            # print('estimate gravity')
            # gravMat = np.zeros(distMatSOM.shape)
            # for n in nodes:
            #     gravMat[nodes.index(n)] = edgeDict[periodIdx]['term'][PRversion][n]
            # gravMat = np.multiply(gravMat,pgrMat)
            # PRprodArray = gravMat.reshape(-1)
            # distMat2 = np.multiply(distMatSOM,distMatSOM)+1
            # distMat2 = distMat2/distMat2.sum()#make sure this complies with the normMethod
            # gravMat = np.divide(gravMat,distMat2)#e-8)
            # gravMat = np.multiply(gravMat,abs(np.identity(gravMat.shape[0])-1))

            # print('Max potential is %s and min potential is %s' %(potentMat.max(),potentMat.min()))
            # print('Max distance is %s and min distance is %s' %(distMatSOM.max(),distMatSOM.min()))
            # print('writing potential matrix to file')
            # with open(potentMatWritePath+'/SOM_potentMat_'+normMethod+'normed_'+years+lvl+'_'+periodIdx+'.tsv', 'w') as d:
            #     d.write('Term\t'+'\t'.join(nodes)+'\n')
            #     for s in nodes:
            #         distLine = [str(float(x)) for x in potentMat[nodes.index(s)].tolist()]
            #         d.write(s+'\t'+'\t'.join(distLine)+'\n')

            # print('Max grav is %s and min grav is %s' %(gravMat.max(),gravMat.min()))
            # print('writing gravity matrix to file')
            # with open(gravMatWritePath+'/SOM_gravMat_'+normMethod+'normed'+years+lvl+'_'+periodIdx+'.tsv', 'w') as d:
            #     d.write('Term\t'+'\t'.join(nodes)+'\n')
            #     for s in nodes:
            #         distLine = [str(float(x)) for x in gravMat[nodes.index(s)].tolist()]
            #         d.write(s+'\t'+'\t'.join(distLine)+'\n')
            # # # #------------------------------------------------------------------------------------------------------------

            # # # #-----------------------------------------------------------------------------------------------------------
            # # # '''potential and gravity plots'''#--------------------------------------------------------------------------
            # # # #-----------------------------------------------------------------------------------------------------------
            # '''plotting heatmap of potential matrix using som'''
            # print('plotting heatmap of potential matrix using som')
                     
            # if not os.path.exists(figWritePath+'/SOM potential Heatmaps'):
            #     os.makedirs(figWritePath+'/SOM potential Heatmaps')
            #     os.makedirs(figWritePath+'/SOM gravity Heatmaps')

            # sns.set(style="darkgrid")
            # fig, ax = plt.subplots()
            # ax = sns.heatmap(potentMat, square = True)#,xticklabels=2,ax=ax)
            # # ax.set_xticks(range(0, len(nodes), 4))#, minor=False)
            # ax.xaxis.tick_top()
            # ax.set_yticklabels(list(reversed(nodes)), minor=False, fontsize = heatMapFont)
            # plt.yticks(rotation=0) 
            # ax.set_xticklabels(nodes, minor=False, fontsize = heatMapFont, rotation = 90)
            # plt.xlabel('SOM potential matrix heatmap (Level '+lvl+' terms | 5 year period prior to '+str(int(periodIdx)*5+trueYearsIni[idy])+')')
            # mng = plt.get_current_fig_manager()
            # mng.window.state('zoomed')
            # interactive(True)
            # plt.show()
            # fig.savefig(figWritePath+'/SOM potential Heatmaps/SOM_potentMatHeatmap_'+normMethod+'normed_'+years+lvl+'_'+periodIdx+'.png',bbox_inches='tight')
            # plt.close()
            # interactive(False)

            # '''plotting heatmap of gravity matrix'''
            # print('plotting heatmap of gravity matrix')            
            # sns.set(style="darkgrid")
            # fig, ax = plt.subplots()
            # ax = sns.heatmap(gravMat, square = True)#,xticklabels=2,ax=ax)
            # # ax.set_xticks(range(0, len(nodes), 4))#, minor=False)
            # ax.xaxis.tick_top()
            # ax.set_yticklabels(list(reversed(nodes)), minor=False, fontsize = heatMapFont)
            # plt.yticks(rotation=0) 
            # ax.set_xticklabels(nodes, minor=False, fontsize = heatMapFont, rotation = 90)
            # plt.xlabel('SOM gravity matrix heatmap (Level '+lvl+' terms | 5 year period prior to '+str(int(periodIdx)*5+trueYearsIni[idy])+')')
            # mng = plt.get_current_fig_manager()
            # mng.window.state('zoomed')
            # interactive(True)
            # plt.show()
            # fig.savefig(figWritePath+'/SOM gravity Heatmaps/SOM_gravMatHeatmap_'+normMethod+'normed_'+years+lvl+'_'+periodIdx+'.png',bbox_inches='tight')
            # plt.close()
            # interactive(False)

            # '''Show as image'''
            # fig = plt.figure()
            # im = plt.imshow(np.log(gravMat), cmap='hot')
            # plt.colorbar(im, orientation='vertical')
            # mng = plt.get_current_fig_manager()
            # mng.window.state('zoomed')
            # plt.title('log10 SOM gravity image (Level '+lvl+' terms | 5 year period prior to '+str(int(periodIdx)*5+trueYearsIni[idy])+')')
            # interactive(True)
            # plt.show()
            # plt.savefig(figWritePath+'/SOM gravity Heatmaps/SOM_gravityImage_'+normMethod+'normed_'+years+lvl+'_'+periodIdx+'.png',bbox_inches='tight')
            # plt.close()
            # interactive(False)
            #------------------------------------------------------------------------------------------------------------


            # #-----------------------------------------------------------------------------------------------------------
            '''GREENWICH based matrix shift'''#---------------------------------------------------------------------------
            # #-----------------------------------------------------------------------------------------------------------
            # somUmatrix =  som.umatrix
            # greenSomUmatrix = somUmatrix.copy()
            # topTerm = edgeDict['topTermsByPR'][0]
            # print(topTerm)
            # topTermCoords = som.bmus[nodes.index(topTerm)]
            # # print(topTermCoords)

            # clmnShift = (n_columns/2) - topTermCoords[0]
            # print('topTermCoords[0]: %s clmnShift: %s' %(topTermCoords[0],clmnShift))
            # rowShift = (n_rows/2) - topTermCoords[1]
            # print('topTermCoords[1]: %s rowShift: %s' %(topTermCoords[1],rowShift))
            # greenSomUmatrix = np.roll(greenSomUmatrix, int(rowShift), axis=0)#int(rowShift)
            # greenSomUmatrix = np.roll(greenSomUmatrix, int(clmnShift), axis=1)#int(clmnShift)

            # '''moving centroids according to greenwich'''
            # xCcG,yCcG = [] ,[]
            # for x in som.centroidBMcoords:                
            #     dimTemp = toroidCoordinateFinder(x[1],clmnShift,x[0],rowShift,n_columns,n_rows)
            #     xCcG.append(dimTemp[0])
            #     yCcG.append(dimTemp[1])

            # print('writing greenwich umatrix to file whose size is: %s' %np.size(greenSomUmatrix))
            # np.savetxt(greenwichUmatrixWritePath+'/umx'+years+lvl+'_'+periodIdx+'.umx',greenSomUmatrix,delimiter='\t', newline='\n',header='% '+ '%s %s'%(n_rows,n_columns))

            # '''Inserting BMUs'''
            # if not os.path.exists(greenwichFigWritePath+'/SOMs/'+SOMdimensionsString+'_epochs'+str(epochs2)):
            #     os.makedirs(greenwichFigWritePath+'/SOMs/'+SOMdimensionsString+'_epochs'+str(epochs2))
            # xDimension, yDimension = [], []
            # for x in som.bmus:
            #     dimTemp = toroidCoordinateFinder(x[0],clmnShift,x[1],rowShift,n_columns,n_rows)
            #     xDimension.append(dimTemp[0])
            #     yDimension.append(dimTemp[1])

            # print('writing BMU coords and names to file')
            # with open(greenwichUmatrixWritePath+'/umx'+years+lvl+'_'+periodIdx+'.bm','w') as f:
            #     with open(greenwichUmatrixWritePath+'/umx'+years+lvl+'_'+periodIdx+'.names','w') as fn:
            #         f.write('% '+'%s %s\n' %(n_rows,n_columns))
            #         fn.write('% '+str(len(nodes))+'\n')
            #         for idx,coox in enumerate(xDimension):
            #             f.write('%s %s %s\n' %(idx,int(yDimension[idx]),int(coox)))
            #             fn.write('%s %s %s\n' %(idx,nodes[idx],nodes[idx]))

            # print('plotting greenwich shifted soms')
            # if not os.path.exists(greenwichFigWritePath+'/Clusters/'+clusterAlgLabel+'/SOMs/'+SOMdimensionsString+'_epochs'+str(epochs2)):
            #         os.makedirs(greenwichFigWritePath+'/Clusters/'+clusterAlgLabel+'/SOMs/'+SOMdimensionsString+'_epochs'+str(epochs2))
            # fig, ax = plt.subplots()
            # plt.pcolor(greenSomUmatrix,cmap = 'gray')
            # ax.scatter(xDimension,yDimension,c=colors,s=areas)
            # doneLabs = set([''])
            # lIdx = 0
            # for label, x, y in zip(originallabels, xDimension, yDimension):
            #     if label == topTerm:
            #         plt.annotate(label, xy = (x, y), xytext = (x, y-lablshift), textcoords = 'data', ha = 'center', va = 'center',bbox = dict(boxstyle = 'round,pad=0.1', fc = 'red'))
            #         topXcoor,topYcoor = x,y
            #         topIdx = lIdx
            #     else:
            #         lblshiftRatio = 2
            #         labFinshift = ''
            #         while labFinshift in doneLabs:
            #             potentialPositions = [(x, y+lablshift), (x+lblshiftRatio*lablshift, y), (x-lblshiftRatio*lablshift, y), (x+lblshiftRatio*lablshift, y+lblshiftRatio*lablshift), 
            #             (x-lblshiftRatio*lablshift, y+lblshiftRatio*lablshift), (x+lblshiftRatio*lablshift, y-lblshiftRatio*lablshift), (x+lblshiftRatio*lablshift, y+lblshiftRatio*lablshift),
            #             (x-lblshiftRatio*lablshift, y+lblshiftRatio*lablshift)]
            #             for pP in potentialPositions:
            #                 labFinshift = pP
            #                 if labFinshift not in doneLabs:
            #                     break
            #             lblshiftRatio+=1
            #         doneLabs.add(labFinshift)
            #         plt.annotate(label, xy = (x, y), xytext = labFinshift, textcoords = 'data', ha = 'center', va = 'center',bbox = dict(boxstyle = 'round,pad=0.1', fc = 'white', alpha = 0.4))#,arrowprops = dict(arrowstyle = '-', connectionstyle = 'arc3,rad=0'))
            #     lIdx+=1

            # plt.scatter(xCcG,yCcG, c= range(len(som.centroidBMcoords)), s= [1000]*len(som.centroidBMcoords), alpha = 0.4)#insert centroids

            # plt.xlim(0,n_columns)
            # plt.ylim(0,n_rows) 
            # # ax.invert_yaxis()
            # plt.gca().invert_yaxis()
            # plt.xlabel('SOM with "'+topTerm.upper()+'" serving as Greenwich. Level '+lvl+' terms, timeslot '+periodIdx+' (5 year period prior to '+str(int(periodIdx)*5+trueYearsIni[idy])+')')
            # mng = plt.get_current_fig_manager()
            # mng.window.state('zoomed')
            # interactive(True)
            # plt.show()            
            # fig.savefig(greenwichFigWritePath+'/Clusters/'+clusterAlgLabel+'/SOMs/'+SOMdimensionsString+'_epochs'+str(epochs2)+'/SOM_AdjMat'+years+lvl+'_'+periodIdx+'.png',bbox_inches='tight')
            # plt.close()
            # interactive(False)
            # # print(greenSomUmatrix.shape())

            # '''Inserting BMUs with WMX code'''
            # xDimension, yDimension = [], []
            # for x in som.bmus:
            #     dimTemp = toroidCoordinateFinder(x[0],clmnShift,x[1],rowShift,n_columns,n_rows)
            #     xDimension.append(dimTemp[0])
            #     yDimension.append(dimTemp[1])
            # fig, ax = plt.subplots()
            # plt.pcolor(greenSomUmatrix,cmap = 'gray')
            # plt.scatter(xDimension,yDimension,c=colors,s=areas)
            # labels = [termLabelDict[" ".join(re.findall("[a-zA-Z]+", nodes[x]))][labelFormat] for x in range(len(xDimension))]
            # doneLabs = set([''])
            # lIdx = 0
            # for label, x, y in zip(labels, xDimension, yDimension):
            #     if lIdx == topIdx:
            #         lIdx+=1
            #         continue
            #     lblshiftRatio = 2
            #     labFinshift = ''
            #     while labFinshift in doneLabs:
            #         potentialPositions = [(x, y+lablshift), (x+lblshiftRatio*lablshift, y), (x-lblshiftRatio*lablshift, y), (x+lblshiftRatio*lablshift, y+lblshiftRatio*lablshift), 
            #         (x-lblshiftRatio*lablshift, y+lblshiftRatio*lablshift), (x+lblshiftRatio*lablshift, y-lblshiftRatio*lablshift), (x+lblshiftRatio*lablshift, y+lblshiftRatio*lablshift),
            #         (x-lblshiftRatio*lablshift, y+lblshiftRatio*lablshift)]
            #         for pP in potentialPositions:
            #             labFinshift = pP
            #             if labFinshift not in doneLabs:
            #                 break
            #         lblshiftRatio+=1
            #     doneLabs.add(labFinshift)
            #     plt.annotate(label, xy = (x, y), xytext = labFinshift, textcoords = 'data', ha = 'center', va = 'center',bbox = dict(boxstyle = 'round,pad=0.1', fc = 'white', alpha = 0.4))#,arrowprops = dict(arrowstyle = '-', connectionstyle = 'arc3,rad=0'))
            #     lIdx+=1
            # plt.annotate(termLabelDict[" ".join(re.findall("[a-zA-Z]+", topTerm))][labelFormat] , xy = (topXcoor, topYcoor), xytext = (topXcoor, topYcoor-lablshift), textcoords = 'data', ha = 'center', va = 'center',bbox = dict(boxstyle = 'round,pad=0.1', fc = 'red'))
            
            # plt.scatter(xCcG,yCcG, c= range(len(som.centroidBMcoords)), s= [1000]*len(som.centroidBMcoords), alpha = 0.4)#insert centroids

            # plt.xlim(0,n_columns)
            # plt.ylim(0,n_rows) 
            # # ax.invert_yaxis()
            # plt.gca().invert_yaxis()
            # plt.xlabel('SOM with "'+topTerm.upper()+'" serving as Greenwich. Level '+lvl+' terms, timeslot '+periodIdx+' (5 year period prior to '+str(int(periodIdx)*5+trueYearsIni[idy])+')')
            # mng = plt.get_current_fig_manager()
            # mng.window.state('zoomed')
            # interactive(True)
            # plt.show()            
            # fig.savefig(greenwichFigWritePath+'/Clusters/'+clusterAlgLabel+'/SOMs/'+SOMdimensionsString+'_epochs'+str(epochs2)+'/SOM_Wmatrix'+labelFormat+'LabeledAdjMat'+years+lvl+'_'+periodIdx+'.png',bbox_inches='tight')
            # plt.close()
            # interactive(False)

            # print('plotting Greenwich umatrix 3D surface') 
            # fig = plt.figure()
            # ax = fig.gca(projection='3d')
            # X = np.arange(0, n_columns, 1)
            # Y = np.arange(0, n_rows, 1)
            # X, Y = np.meshgrid(X, Y)
            # N=greenSomUmatrix/greenSomUmatrix.max()
            # surf = ax.plot_surface(X, Y, greenSomUmatrix, facecolors=cm.jet(N),rstride=1, cstride=1)#,facecolors=cm.jet(somUmatrix) cmap=cm.coolwarm, linewidth=0, antialiased=False)
            # # ax.set_zlim(-1.01, 1.01)
            # # ax.zaxis.set_major_locator(LinearLocator(10))
            # # ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
            # m = cm.ScalarMappable(cmap=cm.jet)
            # m.set_array(greenSomUmatrix)
            # plt.colorbar(m, shrink=0.5, aspect=5)
            # plt.title('Greenwich SOM umatrix 3D surface vizualization (Level '+lvl+' terms | 5 year period prior to '+str(int(periodIdx)*5+trueYearsIni[idy])+')')
            # mng = plt.get_current_fig_manager()
            # mng.window.state('zoomed')
            # interactive(True)
            # plt.show()            
            # fig.savefig(greenwichFigWritePath+'/SOM Umatrices/umxSurf'+years+lvl+'_'+periodIdx+'.png',bbox_inches='tight')
            # plt.close()
            # interactive(False)
            #------------------------------------------------------------------------------------------------------------


        '''pageRank and HITS term fluctuation'''
        # numOfPlots = [5, 10, 20]
        # marker, color = ['*', '+', 'o','d','h','p','s','v','^','d'], ['g','r','m','c','y','k']#line, ["-","--","-.",":"] #list(colors.cnames.keys())
        # marker.sort()
        # color.sort()
        # asmarker = itertools.cycle(marker) 
        # ascolor = itertools.cycle(color) 
        # # asline = itertools.cycle(line) 

        # if not os.path.exists(figWritePath+'/centrality fluctuations over time/PageRank'):
        #     os.makedirs(figWritePath+'/centrality fluctuations over time/PageRank')
        #     os.makedirs(figWritePath+'/centrality fluctuations over time/HITS')
        #     os.makedirs(figWritePath+'/centrality fluctuations over time/Betweenness')

        # allPeriods = list(edgeDict.keys())
        # allPeriods.remove('uniquePersistentTerms')
        # allPeriods.remove('allTerms')            
        # try:
        #     allPeriods.remove('topTermsByPR')
        # except:
        #     pass
        # allPeriods.sort()

        # termPRRankDict = {}
        # termPRSequences = {}
        # termAuthRankDict = {}
        # termAuthSequences = {}
        # termHubRankDict = {}
        # termHubSequences = {}
        # termBetweenRankDict = {}
        # termBetweenSequences = {}
        # for x in nodes:
        #     prSequence, authSequence, hubSequence, betweenSequence = [], [] ,[], []
        #     for p in allPeriods:
        #         prSequence.append(edgeDict[p]['term']['pageRank'][x])
        #         authSequence.append(edgeDict[p]['term']['authority'][x])
        #         hubSequence.append(edgeDict[p]['term']['hub'][x])
        #         betweenSequence.append(edgeDict[p]['term']['betweenness'][x]) 
        #     termPRSequences[x] = prSequence
        #     termPRRankDict[x] = recRank(termPrRanks[x])
        #     termAuthSequences[x] = authSequence
        #     termAuthRankDict[x] = recRank(termAuthRanks[x])
        #     termHubSequences[x] = hubSequence
        #     termHubRankDict[x] = recRank(termHubRanks[x])
        #     termBetweenSequences[x] = betweenSequence
        #     termBetweenRankDict[x] = recRank(termBetweenRanks[x])
        # termPRRanked = sorted(termPRRankDict, key=termPRRankDict.get, reverse=True)
        # termAuthRanked = sorted(termAuthRankDict, key=termAuthRankDict.get, reverse=True)
        # termHubRanked = sorted(termHubRankDict, key=termHubRankDict.get, reverse=True)
        # termBetweenRanked = sorted(termBetweenRankDict, key=termBetweenRankDict.get, reverse=True)

        # edgeDict['topTermsByPR'] = termPRRanked
        # # print(termPRRanked)
        # # edgeDict['termPRRankDict'] = termPRRankDict
        # # print(termPRRankDict)

        # for nop in numOfPlots:

        #     fig, ax = plt.subplots()
        #     for x in termPRRanked[:nop]:
        #         plt.plot(termPRSequences[x], marker=next(asmarker), color=next(ascolor),label=x)
        #     ax.set_xticklabels([int(x)*5+trueYearsIni[idy] for x in allPeriods], minor=False)
        #     ax.legend(loc='upper left',ncol=5)
        #     plt.title('Term PageRank fluctuation over time')
        #     mng = plt.get_current_fig_manager()
        #     mng.window.state('zoomed')
        #     interactive(True)
        #     plt.show()
        #     fig.savefig(figWritePath+'/centrality fluctuations over time/PageRank/top'+str(nop)+'pagerankFlux_'+years+lvl+'.png',bbox_inches='tight')
        #     plt.close()
        #     interactive(False)

        #     fig, ax = plt.subplots()
        #     for x in termAuthRanked[:nop]:
        #         plt.plot(termAuthSequences[x], marker=next(asmarker), color=next(ascolor),label=x)
        #     ax.set_xticklabels([int(x)*5+trueYearsIni[idy] for x in allPeriods], minor=False)
        #     plt.ylim(0, 1.1)
        #     ax.legend(loc='upper left',ncol=5)
        #     plt.title('Term Authority fluctuation over time')
        #     mng = plt.get_current_fig_manager()
        #     mng.window.state('zoomed')
        #     interactive(True)
        #     plt.show()
        #     fig.savefig(figWritePath+'/centrality fluctuations over time/HITS/top'+str(nop)+'authorityFlux_'+years+lvl+'.png',bbox_inches='tight')
        #     plt.close()
        #     interactive(False)

        #     fig, ax = plt.subplots()
        #     for x in termHubRanked[:nop]:
        #         plt.plot(termHubSequences[x], marker=next(asmarker), color=next(ascolor),label=x)
        #     ax.set_xticklabels([int(x)*5+trueYearsIni[idy] for x in allPeriods], minor=False)
        #     plt.ylim(0, 1.1)
        #     ax.legend(loc='upper left',ncol=5)
        #     plt.title('Term Hub fluctuation over time')
        #     mng = plt.get_current_fig_manager()
        #     mng.window.state('zoomed')
        #     interactive(True)
        #     plt.show()
        #     fig.savefig(figWritePath+'/centrality fluctuations over time/HITS/top'+str(nop)+'hubFlux_'+years+lvl+'.png',bbox_inches='tight')
        #     plt.close()
        #     interactive(False)

        #     fig, ax = plt.subplots()
        #     for x in termBetweenRanked[:nop]:
        #         plt.plot(termBetweenSequences[x], marker=next(asmarker), color=next(ascolor),label=x)
        #     ax.set_xticklabels([int(x)*5+trueYearsIni[idy] for x in allPeriods], minor=False)
        #     ax.legend(loc='upper left',ncol=5)
        #     plt.title('Term betweenness fluctuation over time')
        #     mng = plt.get_current_fig_manager()
        #     mng.window.state('zoomed')
        #     interactive(True)
        #     plt.show()
        #     fig.savefig(figWritePath+'/centrality fluctuations over time/betweenness/top'+str(nop)+'BetweenFlux_'+years+lvl+'.png',bbox_inches='tight')
        #     plt.close()
        #     interactive(False)

        pickle.dump(edgeDict,open('./data/artworks_tmp/edgeDictDynamic'+years+lvl+'.pck','wb'), protocol = 2)

        

elapsed = time.time() - t
print('Total time Elapsed: %.2f seconds' % elapsed)
