import data
import numpy as np

def miscall_info(filenames = ["preEjectPitchNonEjectTeam.csv", "preEjectPitchEjectTeam.csv", "postEjectPitchNonEjectTeam.csv", "postEjectPitchEjectTeam.csv"]):
	info_list = [] #used to return all info
	
	for filename in filenames:
		
		info = []
		
		ids = []
		d = data.Data( filename )
		headers = d.get_headers()
		mat = d.get_data(headers)
	
		ab_cs = 0.0
		as_cb = 0.0
		cs = 0.0
		cb = 0.0
		
		total = 0.0
	
		for i in range(mat.shape[0]):
			
			total += 1.0
			
			if mat[i,1] == 1: #if its a called strike
				cs += 1.0
				#if the pitch height is above the top of the strike zone
				#or if the pitch height is below the bottom of the strike zone 
				#or if the pitch's x coord is greater than half the width of the strikezone
				if (mat[i,5] > mat[i,2] or 
				mat[i,5] < mat[i,3] or 
				abs(mat[i,4]) > (17.0/12.0)/2.0):
					ab_cs += 1.0
			elif mat[i,1] == 0: #if its a called ball
				cb += 1.0
				#if the pitch height is below the top of the strike zone
				#and if the pitch height is above the bottom of the strike zone 
				#and if the pitch's x coord is less than half the width of the strikezone
				if (mat[i,5] < mat[i,2] and 
				mat[i,5] > mat[i,3] and 
				abs(mat[i,4]) < (17.0/12.0)/2.0):
					as_cb += 1.0
	
		percent_actual_balls_called_strikes = ab_cs / cs
		percent_actual_strikes_called_balls = as_cb / cb
		percent_miscalls = (ab_cs + as_cb) / total
		
		info.append(percent_actual_balls_called_strikes)
		info.append(percent_actual_strikes_called_balls)
		info.append(percent_miscalls)
		
		info_list.append(info)
		
	return info_list
	
def bayes_probabilities(filenames = ["preEjectPitchNonEjectTeam.csv", "preEjectPitchEjectTeam.csv", "postEjectPitchNonEjectTeam.csv", "postEjectPitchEjectTeam.csv"]):
	#computes the probabilities necessary to apply bayes theorem to our core files
	#similar structure to above
	
	info_list = [] #used to return all info
	
	for filename in filenames:
		
		info = []
		
		d = data.Data( filename )
		headers = d.get_headers()
		mat = d.get_data(headers)
		
		#using floats now to make other operations more readable later
		#also some of these names are flipped around to reflect the probability tree
		cs = 0.0
		cs_as = 0.0
		cs_ab = 0.0
		
		cb = 0.0
		cb_as = 0.0
		cb_ab = 0.0
		
		
		total = 0.0
	
		for i in range(mat.shape[0]):
			
			total += 1.0
			
			#compute the calls first
			
			if mat[i,1] == 1: 
				
				#if its a called strike
				cs += 1.0
				
				#if the pitch height is above the top of the strike zone
				#or if the pitch height is below the bottom of the strike zone 
				#or if the pitch's x coord is greater than half the width of the strikezone
				if (mat[i,5] > mat[i,2] or 
				mat[i,5] < mat[i,3] or 
				abs(mat[i,4]) > (17.0/12.0)/2.0):
					#then it was actually a ball
					cs_ab += 1.0
				
				#else if it actually was a strike
				else:
					cs_as += 1.0
				
			elif mat[i,1] == 0: 
				#if its a called ball
				cb += 1.0
				
				#if the pitch height is below the top of the strike zone
				#and if the pitch height is above the bottom of the strike zone 
				#and if the pitch's x coord is less than half the width of the strikezone
				if (mat[i,5] < mat[i,2] and 
				mat[i,5] > mat[i,3] and 
				abs(mat[i,4]) < (17.0/12.0)/2.0):
					#then it actually was a strike
					cb_as += 1.0
				
				#else if it actually was a ball
				else:
					cb_ab += 1.0
		
		#base rates
		
		p_cs = cs/total
		p_cs_as = cs_as/cs
		p_cs_ab = cs_ab/cs
		
		p_cb = cb/total
		p_cb_as = cb_as/cb
		p_cb_ab = cb_ab/cb
		
		print "-----", filename, "----"
		#bayes theorem calculations
		
		#a called strike being an actual strike
		b_cs_as = (p_cs_as * p_cs) / (p_cs * p_cs_as + p_cb * p_cb_as)
		print "b_cs_as", b_cs_as
		
		#a called strike being an actual ball
		b_cs_ab = (p_cs_ab * p_cs) / (p_cs * p_cs_ab + p_cb * p_cb_ab)
		print "b_cs_ab", b_cs_ab
		
		#a called ball being an actual actual ball
		b_cb_ab = (p_cb_ab * p_cb) / (p_cs * p_cs_ab + p_cb * p_cb_ab)
		print "b_cb_ab", b_cb_ab
		
		#a called ball being an actual strike
		b_cb_as = (p_cb_as * p_cb) / (p_cs * p_cs_as + p_cb * p_cb_as)
		print "b_cb_as", b_cb_as
		
		info.append(b_cs_as)
		info.append(b_cs_ab)
		info.append(b_cb_ab)
		info.append(b_cb_as)
		
		info_list.append(info)
		
	return info_list
	
def anova1(filenames = ["preEjectPitchNonEjectTeam.csv", "preEjectPitchEjectTeam.csv", "postEjectPitchNonEjectTeam.csv", "postEjectPitchEjectTeam.csv"]):
	miscalled_strikes_cols = []
	group_means = []
	group_sizes = []
	
	for filename in filenames:
		d = data.Data( filename )
 		headers = d.get_headers()
 		mat = d.get_data(headers)
 		
 		miscalled_strikes_col = np.matrix(np.zeros(shape=(mat.shape[0],1)))
 		group_sizes.append(mat.shape[0])
 		
 		for i in range(mat.shape[0]):
			if mat[i,1] == 1: 	
			#if its a called strike
				if (mat[i,5] > mat[i,2] or 
				mat[i,5] < mat[i,3] or 
				abs(mat[i,4]) > (17.0/12.0)/2.0):	
				#if it's actually a ball, give our miscalled strikes col a 1
					
					miscalled_strikes_col[i,0] = 1.0
	
		miscalled_strikes_cols.append(miscalled_strikes_col)
		group_means.append(np.mean(miscalled_strikes_col))
	
	grand_mean = np.sum(group_means) / len(filenames)
	#now that we know the grand mean, calculate the total sum of squares
	#total, between and within
	sst = 0.0
	ssw = 0.0
	ssb = 0.0
	for i in range(len(miscalled_strikes_cols)):
		for j in range(miscalled_strikes_cols[i].shape[0]):
			sst += (miscalled_strikes_cols[i][j,0] - grand_mean)**2
			ssw += (miscalled_strikes_cols[i][j,0] - group_means[i])**2
		ssb += ((group_means[i] - grand_mean)**2) * miscalled_strikes_cols[i].shape[0]
	
	#degrees of freedom calculations
	dft = np.sum(group_sizes) - 1
	dfb = len(filenames) - 1
	dfw = 0
	for group_size in group_sizes:
		dfw += group_size - 1
	
	msb = ssb/dfb
	msw = ssw/dfw
	f = msb/msw
	if dfb == 3 and dfw == 39749:
		f_crit = 2.605132610769074 
	elif dfb == 1 and dfw == 19479:
		f_crit = 3.841936257377346
	
	#now to return the information in the display app's expected format
	return [[ssb,dfb,msb,f,f_crit],
			[ssw,dfw,msw],
			[sst,dft]]
	
def anova2(filenames = ["preEjectPitchNonEjectTeam.csv", "preEjectPitchEjectTeam.csv", "postEjectPitchNonEjectTeam.csv", "postEjectPitchEjectTeam.csv"]):
	'''Not the anova computation I ended up using. It followed some less conventional
	methods for getting many of the different parts of the anova table, but the values
	were slightly different. The anova I ended up using is the one above, I included this
	one only because I'm still a bit unsure on the anova process'''
	
	group_means = []
	group_sizes = []
	group_sums = []
	#used for generating grand mean
	total_pitches = 0
	sum_vals = 0
	for filename in filenames:
		d = data.Data( filename )
 		headers = d.get_headers()
 		mat = d.get_data(headers)
 		total_pitches += mat.shape[0]
 		group_sizes.append(mat.shape[0])
 		miscalled_strikes_col = np.matrix(np.zeros(shape=(mat.shape[0],1)))
 		for i in range(mat.shape[0]):
			if mat[i,1] == 1: 
				#if its a called strike
				if (mat[i,5] > mat[i,2] or 
				mat[i,5] < mat[i,3] or 
				abs(mat[i,4]) > (17.0/12.0)/2.0):
					#but it's actually a ball, give our miscalled strikes col a 1
					miscalled_strikes_col[i,0] += 1.0
		group_means.append(np.mean(miscalled_strikes_col))	
		sum_vals += np.sum(miscalled_strikes_col)
		group_sums.append(np.sum(miscalled_strikes_col))
	#our number of groups
	a = len(filenames)
	#total number of observations
	N = np.sum(group_sizes)
	df_between = a - 1
	df_within = N - a
	df_total = N - 1
	
	group_sum_squared_weighted = 0
	t = 0
	for i in range(len(group_sums)):
		group_sum_squared_weighted += group_sums[i]**2 / group_sizes[i]
		t += group_sums[i]
		
	ss_between = group_sum_squared_weighted - (t**2/N)
	ss_within = np.sum(group_sums) - group_sum_squared_weighted
	ss_total = np.sum(group_sums) - (t**2/N)
	ms_between = ss_between / df_between
	ms_within = ss_within / df_within
	f = ms_between / ms_within
	
	#set up our return list
	return [[ss_between,df_between,ms_between,f],
			[ss_within,df_within,ms_within],[ss_total,df_total]]
			
def pre_post_split(filename):
	#used in data pre processing
	ids = []
	d = data.Data( filename )
	headers = d.get_headers()
	mat = d.get_data(headers)
	
	counter = 0.0
	for i in range(mat.shape[0]): # 17 is pre, 18 is called post
		#if mat[i,7] == 17: # pre ejection
		if mat[i,7] == 18: # post ejection
			counter += 1.0
			print counter
			if counter == 1.0:
				pitch_mat = mat[i,:]
			else:
				pitch_mat = np.vstack((pitch_mat,mat[i,:]))
	
	#print pre_mat
		
	np.savetxt("presub.csv", pitch_mat, delimiter=",", fmt="%s")
	
if __name__ == '__main__':	
	#miscall_info()
	#bayes_probabilities()
	anova1()
	