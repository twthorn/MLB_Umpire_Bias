import numpy as np
import datetime as dt
import csv

class Data:
	def __init__(self, filename = None):
		self.filename = filename
		self.full_data = []
		self.raw_data = []
		self.data = []
		self.header2matrix = {}
		self.begin_time = dt.datetime(1970, 1, 1) #used to calculate number of days from

		if self.filename != None:
			self.read_file(self.filename)
			self.process_file()

	def read_file(self, filename):
		f = open(self.filename)
		lines = f.readlines()
		f.close()
		if len(lines) == 1:
			lines = lines[0].split('\r')
		for i in range(len(lines)):
			lines[i] = lines[i].strip().replace(" ", "").split(',')
			self.full_data.append(lines[i])

	def process_file(self):
		self.raw_headers = self.full_data[0]
		self.raw_types = self.full_data[1]
		self.raw_data = self.full_data[2:]
		self.header2raw = {}
		for header in self.raw_headers:
			self.header2raw[header] = len(self.header2raw)

		#set up enum dict and add in keys and values
		self.enum_dict = {}
		counter = 0 #keeps track of unique keys
		for i in range(len(self.raw_types)):
			if self.raw_types[i] == 'enum':
				for j in range(len(self.raw_data)):
					if not self.raw_data[j][i] in self.enum_dict:
						self.enum_dict[self.raw_data[j][i]] = counter
						counter += 1

		#find shape of numeric matrix, which headers to include, and append these
		#headers to self.numeric_headers
		self.numeric_headers = []
		for i in range(len(self.raw_types)):
			if 'numeric' in self.raw_types[i]:
				self.numeric_headers.append(self.raw_headers[i])
			elif 'enum' in self.raw_types[i]:
				self.numeric_headers.append(self.raw_headers[i])
			elif 'date' in self.raw_types[i]:
				self.numeric_headers.append(self.raw_headers[i])
		self.matrix_data = np.matrix(np.zeros(shape=(len(self.raw_data),len(self.numeric_headers))))
		#fill in numeric headers dictionary
		for header in self.numeric_headers:
			self.header2matrix[header] = len(self.header2matrix)

		#fill in the zero matrix with the numeric and enum data from raw_data
		for i in range(len(self.numeric_headers)):
			for j in range(len(self.raw_data)):
				#try various approaches to find the correct strategy for each value
				try:
					#works for numeric data
					self.matrix_data[j,i] = float(self.raw_data[j][self.header2raw[self.numeric_headers[i]]])
					#make sure it moves on to the next one if this method works
					pass
				except:
					try:
						#works for enumerated data
						self.matrix_data[j, i] = float(self.enum_dict[self.raw_data[j][self.header2raw[self.numeric_headers[i]]]])
					except:
						#works for date data, can compute two yyyy/mm/dd and yyyy-mm-dd
						if '/' in self.raw_data[j][self.header2raw[self.numeric_headers[i]]]:
							diff = dt.datetime.strptime(self.raw_data[j][self.header2raw[self.numeric_headers[i]]] , '%Y/%m/%d') - self.begin_time
							self.matrix_data[j,i] = float(diff.days)
						elif '-' in self.raw_data[j][self.header2raw[self.numeric_headers[i]]]:
							diff = dt.datetime.strptime(self.raw_data[j][self.header2raw[self.numeric_headers[i]]] , '%Y-%m-%d') - self.begin_time
							self.matrix_data[j,i] = float(diff.days)

	#accessors	
	def get_raw_headers(self):
		return self.raw_headers

	def get_raw_types(self):
		return self.raw_types

	def get_raw_num_columns(self):
		return len(self.raw_headers)

	def get_raw_num_rows(self):
		return len(self.raw_data)

	def get_raw_row(self, rowindex):
		return self.raw_data[rowindex]

	def get_raw_value(self, rowindex, header):
		return self.raw_data[rowindex][self.header2raw[header]]

	def get_headers(self):
		return self.numeric_headers

	def get_num_columns(self):
		return len(self.header2matrix)

	def get_row(self, rowindex):
		return self.matrix_data[rowindex]

	def get_value(self, rowindex, header):
		return self.matrix_data[rowindex][self.header2matrix[header]]

	def get_data(self, headers):
		#creates correct shape of matrix based on number of headers requested
		if type(headers) != type(['a']):
			headers = [headers]
		matrix = np.matrix(np.zeros(shape=(self.matrix_data.shape[0],len(headers))))
		for y in range(len(headers)):
			for i in range(len(self.numeric_headers)):
				if self.numeric_headers[i] == headers[y]:
					for j in range(len(self.raw_data)):
						matrix[j,y] = self.matrix_data[j,i]
		return matrix

	def add_column(self, datacol, header, datatype):
		#appends a column of data with headers and type
		#to self.full_data which is used in process_data to fill almost every field 
		#if the data is in matrix form convert it to list form for appending to full_data
		if type(datacol) == type(np.matrix([[1,2]])):
			datacol = list(np.array(datacol).reshape(-1,))
			
		datacol.insert(0,header)
		datacol.insert(1,datatype)
		for i in range(len(datacol)):
			self.full_data[i].append(datacol[i])
			
		#calls process_file again to update all other fields with the updated self.full_data
		self.process_file()
		
	def add_row(self, datarow, dataheaders):
		if type(datarow) == type(np.matrix([[1,2]])):
			datarow = list(np.array(datarow).reshape(-1,))
		
		row = []
		for j in range(len(self.numeric_headers)):
			for i in range(len(dataheaders)):
				#find the header from the datarow's headers that matches, and
				#append the correct data in the correct spot
				if dataheaders[i] == self.numeric_headers[j]:
					row.append(datarow[i])
			#if there was no match then add a zero
			if len(row) == j:
				row.append(0.0)
		self.full_data.append(row)
		self.process_file()
	
	def write_data(self, filename):
		np.savetxt(filename, self.full_data, delimiter=",", fmt="%s")

class DataColID:
	def __init__(self, object, header):
		self.object = object
		self.header = header
		#self.index = object.header2raw[header]

	def get_col_data(self):
		return self.object.get_data([self.header])

	def get_header_index(self):
		return self.index


def get_data_from_list(columnIds):
	if len(columnIds) == 0:
		return None
	ret = columnIds[0].object.get_data( columnIds[0].header )
	for colId in columnIds[1:]:
		if colId == None:	
			zeromat = np.matrix(np.zeros(shape=(ret.shape[0],1)))
			ret = np.hstack( (ret, zeromat) ) 
		else:
			ret = np.hstack( (ret,colId.object.get_data( colId.header )) ) 
	return ret



# PCAData objects are mean to hold the results of a PCA transformation
class PCAData(Data):
	def __init__(self,dataColIds,sdata,sdata_mean,pcadata,evals,evecs):
		''' Create a PCAData object with the results of a PCA 
		analysis on the columns identified by dataColIds.
		sdata is the matrix containing the original data.
		sdata_mean is the single-row matrix containing the mean of
		  each column of sdata..
		pcadata contains the original data projected onto the principal
		  components. It is a matrix and ith column contains the data
		  projected onto the ith principal component.
		evals is a single-row matrix containing the eigen values (in order
		  from the largest to the smallest)
		evecs is a matrix containing the eigenvectors associated with each
		  of the evals.
		'''
		Data.__init__(self)

		# set up all the fields in the PCAData object. Instead of 
		# converting from raw data to numeric data as we did in Data.read,
		# here we need to convert from numeric data to raw data.
		self.dataColIds = dataColIds
		self.matrix_data = np.concatenate((pcadata,sdata),1)
		self.raw_data = []
		for i in range(self.matrix_data.shape[0]):
			row = []
			for j in range(self.matrix_data.shape[1]):
				row.append( str(self.matrix_data[i,j]) )
			self.raw_data.append(row)
		self.raw_headers = []
		for i in range( pcadata.shape[1] ):
			self.raw_headers.append( "PC" + str(i) )
		for id in dataColIds:
			self.raw_headers.append( id.header )

		self.raw_types = []
		for i in range( len(self.raw_headers) ):
			self.raw_types.append( 'numeric' )
		self.header2raw = {} # dictionary mapping header string to index of column in raw data
		self.header2matrix = {} # dictionary mapping header string to index of column in matrix data
		for i in range(len(self.raw_headers)):
			self.header2raw[self.raw_headers[i]] = i
			self.header2matrix[self.raw_headers[i]] = i
			#self.num2raw.append(i) 

		# Now we add the extra PCA-related fields.
		self.data_mean = sdata_mean
		self.evals = evals
		self.evecs = np.mat(evecs) # make sure it is a matrix

	def get_eigenvalues(self):
		''' Return a copy of the eigenvalues in a numpy matrix.
		The return value is a single-row matrix'''
		return self.evals.copy()

	def get_eigenvectors(self):
		''' Return a copy of the eigenvectors in a numpy matrix.
		Each eigenvector is a column'''
		return self.evecs.copy()

	def get_data_mean( self ):
		''' Return a single-row matrix containing the mean of each numeric
		column in the original data.'''
		return self.data_mean.copy()

	def get_pca_headers(self):
		''' Return a list of strings naming the headers of the columns
		that contain the data projected onto the principal components.'''
		num_headers = len(self.raw_headers)
		return self.raw_headers[:num_headers/2]

	def get_data_headers(self):
		''' Return a list of strings naming the headers of the columns
		that contain the original data.'''
		num_headers = len(self.raw_headers)
		return self.raw_headers[num_headers/2:]

	def get_headers(self):
		'''Adjusted get_headers function from parent class in order to work with pca, which
		sometimes needs the numeric headers without first processing a file (which the parent
		class uses to setup the numeric headers field)'''
		headers = []
		for i in range(len(self.raw_headers)):
			if self.raw_types[i] == "numeric":
				headers.append(self.raw_headers[i])
		return headers

	def get_data(self, headers):
		'''Adjusted get_data function from parent class in order to work with pca, which 
		sometimes needs to be able to get the data without using the numeric headers set
		up in the process file method'''
		#creates correct shape of matrix based on number of headers requested
		if type(headers) != type(['a']):
			headers = [headers]
		matrix = np.matrix(np.zeros(shape=(self.matrix_data.shape[0],len(headers))))
		for y in range(len(headers)):
			for i in range(len(self.raw_headers)):
				if self.raw_headers[i] == headers[y]:
					for j in range(len(self.raw_data)):
						matrix[j,y] = self.matrix_data[j,i]
		return matrix