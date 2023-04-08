#!/usr/bin/python

import sys

udp2behVersion='1.0'

def printUsage():
    print "********************************************************************************"
    print " udp2beh v"+udp2behVersion
    print " udp2beh is a command line tool which automates the conversion of "
    print " Verilog User Defined Primitives to behavioral code"
    print " Command line arguments : "
    print " udp2beh.py verilogIn verilogOut"
    print "     verilogIn is the input file to be converted"
    print "     verilogOut is the file to write the converted output"
    print "********************************************************************************"

def logMsg(msg):
    print msg

class Primitive(object):
    def __init__(self, primitiveText):
        self.primitiveText = primitiveText
        self._stripComments()
        self._parsePrimitive()

    def _stripComments(self):
        # Strip comments and empty lines
        pos = 0
        while pos<len(self.primitiveText):
            line = self.primitiveText[pos]
            if line.strip()=="":
                self.primitiveText.pop(pos)
                continue
            line = line.split("//")[0]
            if line.strip()=="":
                self.primitiveText.pop(pos)
                continue
            self.primitiveText[pos] = line
            pos += 1
        
    def _parsePrimitive(self):
        self.name = self.primitiveText[0].split("(")[0].split()[1].strip()        

        # Parse ports
        pos = 0
        text = ""
        while ");" not in text:
            text += self.primitiveText[pos]
            pos += 1
        
        text = text.split("(")[1].split(")")[0]
        
        ports = []
        for port in text.split(","):
            ports.append(port.strip())

        inputs = []
        outputs = []
        
        # Find input declarations
        # This way of parsing fails for multi line declarations
        for line in self.primitiveText:
            if line.split()[0].strip()=="input":
                tmp = line.split("input")[1].split(";")[0];
                tmp = tmp.split(",")
                for port in tmp:
                    inputs.append(port.strip())

        # Find output declarations
        # This way of parsing fails for multi line declarations
        for line in self.primitiveText:
            if line.split()[0].strip()=="output":
                tmp = line.split("output")[1].split(";")[0];
                tmp = tmp.split(",")
                for port in tmp:
                    outputs.append(port.strip())
                
        self.inputs = []
        self.outputs = []
        for port in ports:
            if port in inputs:
                self.inputs.append(port)
            if port in outputs:
                self.outputs.append(port)

        if len(self.outputs)!=1:
            logMsg("ERROR: Primitive "+self.name+" has "+str(len(self.outputs))+" outputs != 1")
            sys.exit(1)

        # Parse table
        tableText = []
        foundTable = False
        inTable = False
        for line in self.primitiveText:
            if not inTable:
                if line.strip()=="table":
                    foundTable=True
                    inTable=True
            else:
                if line.strip()=="endtable":
                    inTable=False
                else:
                    tableText.append(line.split(";")[0])

        if not foundTable:
            logMsg("ERROR: Table not found in primitive "+self.name)
            sys.exit(1)

        if inTable:
            logMsg("ERROR: Table unexpectedly ended in primitive "+self.name)
            sys.exit(1)

        numEnt = len(tableText[0].split(":"))

        if numEnt==3:
            self.type = "SEQ"
        elif numEnt==2:
            self.type = "COMB"
        else:
            logMsg("ERROR: Malformed table in primitive "+self.name)
            sys.exit(1)
        
        for tmp in tableText:
            if len(tmp.split(":"))!=numEnt:
                logMsg("ERROR: Malformed table in primitive "+self.name)
                sys.exit(1)
        
        table = []
        for line in tableText:
            ins = line.split(":")[0]
            insSplit = ins.split()
            if len(insSplit) != len(self.inputs):
                logMsg("ERROR: Malformed table in primitive "+self.name)
                sys.exit(1)
                
            tableInputs = []
            for tmp in insSplit:
                tableInputs.append(tmp.strip())

            out = line.split(":")[1].strip()
            
            if numEnt==3:
                next = line.split(":")[2].strip()
                
            if numEnt==2:
                table.append( (tableInputs, out) )
            else:
                table.append( (tableInputs, out, next) )
                
        self.table = table
        self.generateVerilog()      
        #print self.strTable()      
        #for line in self.generateVerilog():
        #    print line

    def generateVerilog(self):
        if self.type=="COMB":
            return self._generateCombinatorial()
        else:
            return self._generateSequential()

    def _generateModuleHeader(self):
        res = []
        tmp = "module "+self.getName()+" ("
        for output in self.outputs:
            tmp += output + ","
        for inp in self.inputs:
            tmp += inp + ","
        
        tmp = tmp[:-1]
        tmp += ");"
        res.append(tmp)

        tmp = "\toutput "
        for output in self.outputs:
            tmp += output + ","
        tmp = tmp[:-1]
        tmp += ";"
        
        res.append(tmp)
        
        tmp = "\treg "
        for output in self.outputs:
            tmp += output + ","
        tmp = tmp[:-1]
        tmp += ";"
        
        res.append(tmp)
        
        tmp = "\tinput "
        for inp in self.inputs:
            tmp += inp + ","
        tmp = tmp[:-1]
        tmp += ";"
        
        res.append(tmp)
        return res    


    def _generateCombinatorial(self):
        res = []
        
        for line in self._generateModuleHeader():
            res.append(line)
            
        res.append("\talways @(*)")
        
        tmp = "\tcasez ({"
        for inp in self.inputs:
            tmp += inp + ","
        tmp = tmp[:-1]
        tmp += "})"
        
        res.append(tmp)
        
        nInputs = len(self.inputs)
        
        for tableRow in self.table:
            tmp = "\t\t"+str(nInputs)+"'b"
            for inp in tableRow[0]:
                tmp += inp
            tmp += " : " + self.outputs[0] + " = 1'b" + tableRow[1] + ";"
            res.append(tmp)
        res.append("\tendcase")
        res.append("endmodule")
        return res                

    def _isEdgeSensitive(self, inputs):
        # Check if there is egde sensitive input
        if self._risingSensitive(inputs)>-1:
            return True
        if self._fallSensitive(inputs)>-1:
            return True
        return False

    def _risingSensitive(self, inputs):
        # Return rising sensitive input number or -1 if none
        if 'r' in inputs:
            return inputs.index('r')
        if '(01)' in inputs:
            return inputs.index('(01)')
        if 'p' in inputs:
            return inputs.index('p')
        if '(0x)' in inputs:
            return inputs.index('(0x)')
        if '(x1)' in inputs:
            return inputs.index('(x1)')
        if '(1z)' in inputs:
            return inputs.index('(1z)')
        if '(z1)' in inputs:
            return inputs.index('(z1)')
        if '*' in inputs:
            return inputs.index('*')
        return -1    

    def _fallSensitive(self, inputs):
        # Return fall sensitive input number or -1 if none
        if 'f' in inputs:
            return inputs.index('f')
        if '(10)' in inputs:
            return inputs.index('(10)')
        if 'n' in inputs:
            return inputs.index('n')
        if '(1x)' in inputs:
            return inputs.index('(1x)')
        if '(x0)' in inputs:
            return inputs.index('(x0)')
        if '(0z)' in inputs:
            return inputs.index('(0z)')
        if '(z0)' in inputs:
            return inputs.index('(z0)')
        if '*' in inputs:
            return inputs.index('*')
        return -1    

    def _generateLevelSensitiveValues(self,inputs, out):
        pos = 0
        levelInputs = "{"
        tableValues = ""
        while pos<len(inputs):
            if inputs[pos] != "?":
                levelInputs += self.inputs[pos]+","
                tableValues += inputs[pos]
            pos += 1
        if out != "?":
            levelInputs += self.outputs[0]+","
            tableValues += out
        if len(tableValues)>0:    
            levelInputs = levelInputs[:-1] + "}"
            tableValues = str(len(tableValues))+"'b"+tableValues
        else:
            levelInputs = "1'b1"
            tableValues = "1'b1"
            
        return (levelInputs, tableValues)

    def _generateEdgeSensitiveValues(self,inputs, out, edgeNum):
        pos = 0
        levelInputs = "{"
        tableValues = ""
        while pos<len(inputs):
            if inputs[pos] != "?" and pos!=edgeNum:
                levelInputs += self.inputs[pos]+","
                tableValues += inputs[pos]
            pos += 1
        if out != "?":
            levelInputs += self.outputs[0]+","
            tableValues += out
        if len(tableValues)>0:                
            levelInputs = levelInputs[:-1] + "}"
            tableValues = str(len(tableValues))+"'b"+tableValues
        else:
            levelInputs = "1'b1"
            tableValues = "1'b1"

        return (levelInputs, tableValues)
        
    def _generateSequential(self):
        res = []

        # Generate module header
        for line in self._generateModuleHeader():
            res.append(line)

        
        # Perform table reduction
        pos = 0
        while pos<len(self.table):
            inputs, out, next = self.table[pos]
            if next == "-":
                self.table.pop(pos)
                continue
            if next == out:
                self.table.pop(pos)
                continue
            pos += 1


        eventDetectors = []
        outputAssignments = []
        regDefs = []
        
        eventNo = 0
        for tableRow in self.table:
            inputs, out, next = tableRow
            
            if self._isEdgeSensitive(inputs):
                # Edge sensitive table entry
                nRising = self._risingSensitive(inputs)
                if nRising>-1:
                    regDefs.append("reg event_"+str(eventNo)+";")
                    regDefs.append("reg event_"+str(eventNo)+"_clear;")
                
                    edgeSignal = self.inputs[nRising]
                    edgeInputs, tableValues = self._generateEdgeSensitiveValues(inputs, out, nRising)
                    
                    eventDetectors.append("always @(posedge "+edgeSignal+" or posedge event_"+str(eventNo)+"_clear)")
                    eventDetectors.append("begin")
                    eventDetectors.append("\tif (event_"+str(eventNo)+"_clear)")
                    eventDetectors.append("\t\t event_"+str(eventNo)+" = 0;")
                    eventDetectors.append("\telse if ("+edgeInputs+" == "+tableValues+")")
                    eventDetectors.append("\t\t event_"+str(eventNo)+" = 1;")
                    eventDetectors.append("end")
                    
                    outputAssignments.append("if (event_"+str(eventNo)+")")
                    outputAssignments.append("begin")
                    outputAssignments.append("\t"+self.outputs[0]+"=1'b"+next+";")
                    outputAssignments.append("\tevent_"+str(eventNo)+"_clear = 1;")                    
                    outputAssignments.append("end")
                    outputAssignments.append("else")
                    outputAssignments.append("\tevent_"+str(eventNo)+"_clear = 0;")

                    eventNo += 1

                nFall = self._fallSensitive(inputs)
                if nFall>-1:
                    regDefs.append("reg event_"+str(eventNo)+";")
                    regDefs.append("reg event_"+str(eventNo)+"_clear;")
                
                    edgeSignal = self.inputs[nFall]
                    edgeInputs, tableValues = self._generateEdgeSensitiveValues(inputs, out, nFall)
                    
                    eventDetectors.append("always @(negedge "+edgeSignal+" or posedge event_"+str(eventNo)+"_clear)")
                    eventDetectors.append("begin")
                    eventDetectors.append("\tif (event_"+str(eventNo)+"_clear)")
                    eventDetectors.append("\t\t event_"+str(eventNo)+" = 0;")
                    eventDetectors.append("\telse if ("+edgeInputs+" == "+tableValues+")")
                    eventDetectors.append("\t\t event_"+str(eventNo)+" = 1;")
                    eventDetectors.append("end")
                    
                    outputAssignments.append("if (event_"+str(eventNo)+")")
                    outputAssignments.append("begin")
                    outputAssignments.append("\t"+self.outputs[0]+"=1'b"+next+";")
                    outputAssignments.append("\tevent_"+str(eventNo)+"_clear = 1;")                    
                    outputAssignments.append("end")
                    outputAssignments.append("else")
                    outputAssignments.append("\tevent_"+str(eventNo)+"_clear = 0;")

                    eventNo += 1
                
            else:
                # Level sensitive table entry
                levelInputs, tableValues = self._generateLevelSensitiveValues(inputs, out)
                
                regDefs.append("reg event_"+str(eventNo)+";")
                eventDetectors.append("always @(*)")
                eventDetectors.append("begin")
                eventDetectors.append("\tif ("+levelInputs+" == " + tableValues +")")
                eventDetectors.append("\t\tevent_"+str(eventNo)+" = 1;")
                eventDetectors.append("\telse")
                eventDetectors.append("\t\tevent_"+str(eventNo)+" = 0;")
                eventDetectors.append("end")

                outputAssignments.append("if (event_"+str(eventNo)+")")
                outputAssignments.append("\t"+self.outputs[0]+"=1'b"+next+";")

                eventNo += 1

        for entry in regDefs:
            res.append("\t"+entry)

        
        for entry in eventDetectors:
            res.append("\t"+entry)
            
        res.append("\talways @(*)")
        res.append("\tbegin")
        for entry in outputAssignments:
            res.append("\t\t"+entry)
        res.append("\tend")
        
        res.append("endmodule")
        return res                

                
    def fillSpace(self, inp, nSpace=10):
        if len(inp)<nSpace:
            nSpace = nSpace-len(inp)
        else:
            nSpace = len(inp)+2
        if nSpace%2==1:
           return " "*int(nSpace/2)+inp+" "*int(nSpace/2+1)
        else:
           return " "*int(nSpace/2)+inp+" "*int(nSpace/2)            


    def strTable(self):
        res = ""
        
        nSpaces = []
        for inp in self.inputs:
            n = len(inp)+1
            if n<5:
                n = 5
            nSpaces.append(n)

        nSpaces.append(len(self.outputs[0])+1)
        
        if self.type=="SEQ":
            nSpaces.append(len(self.outputs[0])+1)
        
        pos = 0
        for inp in self.inputs:
            res += self.fillSpace(inp, nSpaces[pos])
            pos += 1
        
        res += ": "
        res += self.fillSpace(self.outputs[0], nSpaces[pos])
        pos += 1
        if self.type=="SEQ":
            res += ": "
            res += self.fillSpace(self.outputs[0], nSpaces[pos])
        
        res += "\n"
        for tblRow in self.table:
            pos = 0
            if self.type=="SEQ":
                inputs, out, next = tblRow
                for inp in inputs:
                    res += self.fillSpace(inp, nSpaces[pos])
                    pos += 1
                res += ": "
                res += self.fillSpace(out, nSpaces[pos])
                pos += 1
                res += ": "
                res += self.fillSpace(next, nSpaces[pos])
            else:
                inputs, out = tblRow
                for inp in inputs:
                    res += self.fillSpace(inp, nSpaces[pos])
                    pos += 1
                res += ": "
                res += self.fillSpace(out, nSpaces[pos])
            res += "\n"
        return res

    def getName(self):
        return self.name        

    def getInputs(self):
        return self.inputs
        
    def getOutputs(self):
        return self.outputs
        
    def getType(self):
        return self.type

def getUDPs(sourceVerilog):
    # Finds and removes primitive from sourceVerilog
    # Returns a list of primitive UDPs
    
    primitiveUDPs = []

    pos = 0

    while pos<len(sourceVerilog):
        line = sourceVerilog[pos]
        if line.strip()=="":
            pos += 1
            continue
        keyword = line.split()[0].strip()
        if keyword=="primitive":
            # Found primitive
            print("found primitive")
            primitiveText = [line]
            sourceVerilog.pop(pos)
            while pos<len(sourceVerilog):
                line = sourceVerilog[pos]
                sourceVerilog.pop(pos)
                if line.strip()=="":
                    continue
                x = line.find("//")
                y = line.strip().find("endprimitive")
                if x!=-1 and y != -1 and y<x:
                    line = line[0:x].strip()
                primitiveText.append(line)
                if line.strip()=="endprimitive":
                    print(line)
                    break
                
            if pos==len(sourceVerilog) and line.strip()!="endprimitive":
                logMsg("Unexpected end of file. Expected endprimitive.")
                sys.exit(1)
            
            primitiveUDPs.append( Primitive(primitiveText) )
        else:
            pos += 1    

    return primitiveUDPs

def udp2beh(verilogInFile, verilogOutFile):
    tmpStr = "udp2beh v"+udp2behVersion    
    logMsg("\t\t\t"+"*"*int(len(tmpStr)+4))
    logMsg("\t\t\t*"+" "*int(len(tmpStr)+2)+"*")
    logMsg("\t\t\t* udp2beh v"+udp2behVersion+" *")
    logMsg("\t\t\t*"+" "*int(len(tmpStr)+2)+"*")
    logMsg("\t\t\t"+"*"*int(len(tmpStr)+4))

    logMsg("")
    logMsg("Reading source Verilog file : "+verilogInFile)
    logMsg("")
        
    # Read the input file
    sourceVerilog = []
    
    inFile = open(verilogInFile, 'r')
    for line in inFile:
        sourceVerilog.append(line)
    inFile.close()    

    # Find and remove primitive UDPs from source Verilog
    primitiveUDPs = getUDPs(sourceVerilog)
    
    nPrimitives = len(primitiveUDPs)
    if nPrimitives==0:
        logMsg("No primitives found. Output is equal to input")
        outFile=open(verilogOutFile, 'w')
        for line in sourceVerilog:
            outFile.write(line)
        outFile.close()    
    else:
        logMsg("Found "+str(nPrimitives)+" primitives :")
        for primitive in primitiveUDPs:
            logMsg("\t"+primitive.getName()+"\t"+primitive.getType())
    

        for primitive in primitiveUDPs:
            logMsg("")
            logMsg("-----------------------------------------------------")
            logMsg("Processing primitive "+primitive.getName()+" of type "+primitive.getType())
            logMsg("")
            logMsg("Reduced primitive table : ")
            logMsg(primitive.strTable())
            logMsg("")
            logMsg("Generated Verilog code : ")
            for line in primitive.generateVerilog():
                logMsg(line)
        logMsg("-----------------------------------------------------")

    # If primitive was not named, assign name to module
    pos = 0
    while pos<len(sourceVerilog):
        line = sourceVerilog[pos]
        if line.strip()=="":
            pos += 1
            continue
        tmp = line.split()
        for primitive in primitiveUDPs:
            if tmp[0].strip()==primitive.getName():
                if tmp[1].strip()[0]=="(":
                    # Primitive was not named
                    line_new = line.replace(primitive.getName(), primitive.getName()+" "+primitive.getName()+"_inst"+str(pos))
                    sourceVerilog[pos] = line_new
                    break
        pos += 1
        
    logMsg("")
    logMsg("Writing output to : "+verilogOutFile)

    outFile=open(verilogOutFile, 'w')
    for line in sourceVerilog:
        outFile.write(line)
    for primitive in primitiveUDPs:
        for line in primitive.generateVerilog():
            outFile.write(line+"\n")
    outFile.close()    

########################################################################################
# Main
########################################################################################
if len(sys.argv) != 3:
    printUsage()
    exit(-1)

verilogInFile = sys.argv[1]
verilogOutFile = sys.argv[2]

exit(udp2beh(verilogInFile, verilogOutFile))

