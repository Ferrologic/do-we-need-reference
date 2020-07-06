import numpy as np

class Matriz:
    
    def __init__(self, rows = None, columns = None):
        if rows is None or columns is None:
            self.matriz = []
            self.sizeRows = 0
            self.sizeColumns = 0
        else:
            self.matriz = [[0 for x in range(columns)] for y in range(rows)] 
            self.sizeRows = rows
            self.sizeColumns = columns
    
    def add(self, row, column, value):
        self.matriz[row][column] = value
        
    def transpose(self):
        tmpM = Matriz(len(self.matriz[0]),len(self.matriz))
        for r in range(0,len(self.matriz)):
            for c in range(0,len(self.matriz[0])):
                tmpM.add(c,r,self.get(r,c))
        return tmpM
    
    def matmul(self,A,B):
        tmpM = Matriz(len(A.matriz),len(B.matriz[0]))
        for r in range(0,len(A.matriz)):
            for c in range(0,len(B.matriz[0])):
                sum = 0
                for k in range(0,len(A.matriz[0])):
                    sum += A.get(r,k) * B.get(k,c)
                tmpM.add(r,c,sum)
        return tmpM
    
    def inverse(self):
        tmpM = Matriz(len(self.matriz),len(self.matriz[0]))
        #print(self.determinant(self))
        tmpM = self.adj(self).multconst(self, 1/self.determinant(self)).transpose()
        #tmpM = tmpM.transpose()
        return tmpM
    
    def multconst(self, inM, v):
        tmpM = Matriz(len(inM.matriz),len(inM.matriz[0]))
        for i in range(0, len(inM.matriz)):
            for j in range(0, len(inM.matriz[0])):
                tmpM.add(i,j,self.get(i,j)*v)
        return tmpM
    
    def adj(self, inM):
        tmpM = Matriz(len(inM.matriz),len(inM.matriz[0]))
        for i in range(0,len(inM.matriz)):
            for j in range(0,len(inM.matriz[0])):
                r = []
                r.append(i)
                c = []
                c.append(j)
                svar = pow(-1,i+j)*self.determinant(self.sub_matriz_elim(inM,r,c))
                tmpM.add(i,j,svar)
        return tmpM
                
    def determinant(self, inM):
        if inM.sizeRows == 1:
            return inM.get(0,0)
        elif inM.sizeRows == 2:
            return (inM.get(0,0)*inM.get(1,1)-inM.get(0,1)*inM.get(1,0))
        else:
            tempresult = 0
            for i in range(0,len(inM.matriz[0])):
                rows = []
                rows.append(0)
                columns = []
                columns.append(i)
                d = self.determinant(self.sub_matriz_elim(inM,rows,columns))
                e = pow(-1,i)
                f = inM.get(0,i)
                tempresult += (f*e*d)
                #print(d,e,f)
        return tempresult

    
    def sub_matriz_elim(self, inM, rows, columns):
        tmpM = Matriz(inM.sizeRows - len(rows), inM.sizeColumns - len(columns))
        newRows = -1
        newColumns = -1
        for i in range(0,inM.sizeRows):
            if i in rows:
                continue
            else:
                newRows += 1
            
            newColumns = -1
            for j in range(0,inM.sizeColumns):
                if j in columns:
                    continue
                else:
                    newColumns += 1
                tmpM.add(newRows,newColumns,inM.get(i,j))
        return tmpM
    
    def displayMatriz(self):
        for row in self.matriz:
            print(row)
        
    def get(self, row, column):
        return self.matriz[row][column]
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        