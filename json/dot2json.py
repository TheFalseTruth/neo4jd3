import re
import sys

INDENT = '\t'
NODE_MAPPING = {}
RELATIONSHIP_QUEUE = list()
NODE_TYPE = ["ENTRY_POINT", "EXPRESSION", "NEW VARIABLE", "END_IF", "IF"]

class Node:
    def __init__(self, id, label, description):
        self.id = id
        self.label = label
        self.description = description

    def __str__(self):
        return f'{INDENT*5}"id": "{self.id}",\n{INDENT*5}"labels": ["{self.label}"],\n{INDENT*5}"properties": {{\n{INDENT*5}\t"IRs": "{self.description}"\n{INDENT*5}}}\n'

class Relationship:
    def __init__(self, id, startNode, endNode, typeRelationship = None):
        self.id = id
        self.startNode = startNode
        self.endNode = endNode
        self.type = typeRelationship

    def __str__(self):
        if (self.type is not None):
            return f'{INDENT*5}"id": "{self.id}",\n{INDENT*5}"startNode": "{self.startNode}",\n{INDENT*5}"endNode": "{self.endNode}",\n{INDENT*5}"type": "{self.type}"\n'
        else:
            return f'{INDENT*5}"id": "{self.id}",\n{INDENT*5}"startNode": "{self.startNode}",\n{INDENT*5}"endNode": "{self.endNode}"\n'


def processNode(node, isEndPoint = False):
    # Get node ID
    regexGetNodeID = re.compile('[0-9]+\[')
    nodeID = regexGetNodeID.search(node).group().replace('[', '')
    
    # Get node label
    regexNodeLabel = re.compile('\"[\s\S]*\"')
    nodeLabel = regexNodeLabel.search(node).group().replace('"', '').split('\n\n')

    # print(nodeLabel)
    
    # Get Node definition 
    nodeType = nodeLabel[0].split(': ')[1].replace('\n', '') 
    
    nodeClass = 'OTHERS'
    for i in range(0, len(NODE_TYPE)):
        if (NODE_TYPE[i] in nodeType):
            nodeClass = NODE_TYPE[i]
            break

    # Get all remaining information
    nodeExpr = ''
    description = ''

    if (len(nodeLabel) > 1):
        nodeExpr = nodeLabel[1].replace('\n', ' ').split(': ')[1]

        description = nodeLabel[2].replace('\n', ';').split(':;')[1]
    else: # For (END_IF and ENTRY_POINT)
        nodeExpr = nodeType
        
    # Map to nodeID
    NODE_MAPPING[nodeID] = [nodeExpr, nodeClass]

    return Node(nodeExpr, nodeClass, description) if not isEndPoint else Node(nodeExpr, "END_POINT", description)
def processRelationship(relationship, id):
    nodeIdList = relationship.replace('\n', '').split('->') # Holds startNode and endNode
    
    # Get node startNode EXP
    startNode = NODE_MAPPING[nodeIdList[0]][0]

    # Get the endNode EXP 
    endNode = NODE_MAPPING[nodeIdList[1]][0]

    # print(startNode + ' ' + endNode)

    typeRelationship = NODE_MAPPING[nodeIdList[0]][1]

    if (typeRelationship == "IF"):
        return Relationship(id + 1, startNode, endNode, typeRelationship)
    else:
        return Relationship(id + 1, startNode, endNode)

    

def convert(fileName):
    data = ""
    with open(fileName, 'r') as dotFile:
        for line in dotFile:
            if line == "digraph{\n" or line == "}\n":
                continue
            data += line
        # data = data.replace('\n', ' ')
        data = data.split(';')

        del data[-1] # Remove last element

        dotFile.close()

    # print(data)

    nodeList = list()
    relationshipList = list()

    # description = ""
    regex = re.compile('[0-9]+->[0-9]+') # Regex to detect relationship


    for i in range(0, len(data)):
        # If data is a Node definition
        if regex.search(data[i]) == None and i == len(data) - 1:
            nodeList.append(processNode(data[i], True))
        elif regex.search(data[i]) == None:
            nodeList.append(processNode(data[i]))    
        else:
            RELATIONSHIP_QUEUE.append(data[i])

    # We need all node definition first, kinda slow performance
    for i in range(0, len(RELATIONSHIP_QUEUE)):
        relationshipList.append(processRelationship(RELATIONSHIP_QUEUE[i], len(relationshipList)))


    nodesJSON = f'\n{INDENT*4}"nodes": ['
    relationshipJSON = f'{INDENT*4}"relationships": ['

    for i in range(0, len(nodeList)):
        if i == len(nodeList) - 1:
            nodesJSON += f'{{\n{str(nodeList[i])}{INDENT*4}}}],\n'
            continue
        else:
            nodesJSON += f'{{\n{str(nodeList[i])}{INDENT*4}}}, '


    for i in range (0, len(relationshipList)):
        if i == len(relationshipList) - 1:
            relationshipJSON += f'{{\n{str(relationshipList[i])}{INDENT*4}}}]\n'
            continue
        else:
            relationshipJSON += f'{{\n{str(relationshipList[i])}{INDENT*4}}}, '


    jsonStart = f'{{\n{INDENT}"results": [{{\n{INDENT*2}"columns": ["user", "entity"],\n{INDENT*2}"data": [{{\n{INDENT*3}"graph": {{\n'

    jsonEnd = f'{INDENT*3}}}\n{INDENT*2}}}]\n{INDENT}}}],\n{INDENT}"errors": []\n}}'

    result = jsonStart + nodesJSON + relationshipJSON + jsonEnd


    with open('resultData[2].json', 'w') as outputFile:
        outputFile.write(result)
        outputFile.close()

def main():
    if len(sys.argv) != 2:
        print(f'Usage: python dot2json.py [dot file]')
        exit(-1)
    else:
        convert(sys.argv[1])

if __name__ == '__main__':
    try:
        main()
    except IOError as e:
        print(f'Cannot open file {e.filename}: {e.strerror}')
        exit(-1)