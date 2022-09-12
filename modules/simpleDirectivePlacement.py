import json
from math import floor, log2

HLS_SRC_INFO = 'src_info.json'
HLS_KRN_INFO = 'kernel_info.txt'

UNROLL_ITERATION_LIM = 16
ARRAY_PARTITION_LIM = 4096

def treeTraversalUnroll(loop,LoopDict,DirectiveDict,translationDict):
    currentLoop = LoopDict[loop]
    if currentLoop['Innermost']:
        if currentLoop['LoopLimActual'] <= UNROLL_ITERATION_LIM and currentLoop['LoopLimActual'] > 0:
            DirectiveDict[loop] = [('loop','unroll',currentLoop['LoopLimActual'])]
            return True
        else:
            return False
    else:
        AllSubloopsUnrolled = True
        for subloopUID in currentLoop['Subloops']:
            if not subloopUID in translationDict: continue
            translatedLoop = translationDict[subloopUID]
            if not treeTraversalUnroll(translatedLoop,LoopDict,DirectiveDict,translationDict):
                AllSubloopsUnrolled = False
        if AllSubloopsUnrolled and currentLoop['LoopLimActual'] <= UNROLL_ITERATION_LIM:
            DirectiveDict[loop] = [('loop','unroll',currentLoop['LoopLimActual'])]
            return True
        else:
            return False

def PipelinePlacement(LoopDict,DirectiveDict,translationDict):
    for loop in LoopDict:
        if LoopDict[loop]['Innermost']:
            if loop in DirectiveDict:
                DirectiveDict[loop].append(('loop','pipeline'))
            else:
                DirectiveDict[loop] = [('loop','pipeline')]
        else:
            FullyUnrolledSubloops = True
            for subloop in LoopDict[loop]['Subloops']:
                if not subloop in translationDict: continue
                translatedLoop = translationDict[subloop]
                if not translatedLoop in DirectiveDict or not 'unroll' in DirectiveDict[translatedLoop]:
                    FullyUnrolledSubloops = False
                    break
            if FullyUnrolledSubloops:
                if loop in DirectiveDict:
                    DirectiveDict[loop].append(('loop','pipeline'))
                else:
                    DirectiveDict[loop] = [('loop','pipeline')]


def ArrayPartitionPlacement(ArrayDict,DirectiveDict):
    for array in ArrayDict:
        elements = ArrayDict[array]
        totalElements = 1
        for element in elements: totalElements *= int(element)
        if totalElements < ARRAY_PARTITION_LIM: DirectiveDict[f"{array}\n"] = [('array','partition','full',ARRAY_PARTITION_LIM)]
        else: DirectiveDict[f"{array}\n"] = [('array','partition','partial',ARRAY_PARTITION_LIM)]

def loopUnroller(loopLim):
    results = []
    pow2 = floor(log2(loopLim))
    for i in range(1,pow2+1):
        results.append(f"#pragma HLS unroll factor={2**i}")
    if 2**pow2 != loopLim:
        results.append('#pragma HLS unroll')
    return results

def arrayPartitioner(arrayLim,varName):
    results = []
    pow2 = floor(log2(arrayLim))
    for i in range(1,pow2+1):
        results.append(f"#pragma HLS array_partition variable={varName} type=cyclic factor={2**i} dim=1")
    return results

def directiveConstructor(analysisItem,tag,backupKrnl):
    if analysisItem[0] == 'loop':
        if analysisItem[1] == 'pipeline':
            return [f"#pragma HLS pipeline"]
        elif analysisItem[1] == 'unroll':
            return list(loopUnroller(analysisItem[2]))
        return []
    elif analysisItem[0] == 'array':
        name = backupKrnl[tag][1]
        tempRes = arrayPartitioner(analysisItem[3],name)
        if analysisItem[2] == 'full':
            tempRes.append(f"#pragma HLS array_partition variable={name} type=complete")
        return tempRes
        

def simpleDirectiveBuilder(src_krn_directory):
    with open(f"{src_krn_directory}/{HLS_SRC_INFO}",'r') as srcInfo:
        sourceInfo = json.load(srcInfo)

    krnlInfoLines = []
    with open(f"{src_krn_directory}/{HLS_KRN_INFO}",'r') as krnl_info:
        krnlInfoLines = krnl_info.readlines()

    #print(sourceInfo)

    krnlName = krnlInfoLines[0]
    arrays = {}
    loops = []
    backupKernelInfoDict = {}
    for line in krnlInfoLines[1:]:
        tmp = line[:-1].split(',')
        if tmp[1] == 'loop':
            loops.append(tmp[0])
        else:
            arrays[tmp[0]] = list(tmp[4::2])
        backupKernelInfoDict[tmp[0]] = list(tmp[1:])

    # Create loop <-> UID dictionary mapping

    loopUIDMap = {}
    for loop in sourceInfo['loops']:
        loopUIDMap[sourceInfo['loops'][loop]["UID"]] = loop

    DirectiveDict = {}

    for loop in sourceInfo['loops']:
        if sourceInfo['loops'][loop]['Outermost']:
            treeTraversalUnroll(loop,sourceInfo['loops'],DirectiveDict,loopUIDMap)

    PipelinePlacement(sourceInfo['loops'],DirectiveDict,loopUIDMap)
    ArrayPartitionPlacement(arrays,DirectiveDict)
    #print(f"\n\n\n{DirectiveDict}")

    FDirectiveDict = {}
    for i in range(1,len(krnlInfoLines[1:])+1):
        if f"L{i}\n" in DirectiveDict:
            FDirectiveDict[f"L{i}"] = DirectiveDict[f"L{i}\n"]
        else:
            FDirectiveDict[f"L{i}"] = []

    #print(FDirectiveDict)


    FinalDirectives = []
    for i in range(1,len(krnlInfoLines[1:])+1):
        analysisResults = FDirectiveDict[f"L{i}"]
        availableDirectives = []
        for item in analysisResults:
            availableDirectives.extend(list(directiveConstructor(item,f"L{i}",backupKernelInfoDict)))
        FinalDirectives.append(list(availableDirectives))




# Fetch your results from FinalDirectives



