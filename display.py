import Tkinter as tk
import numpy as np
import random
import data
import strikeZoneAnalysis

class DisplayApp:
	def __init__(self, width, height):
		self.root = tk.Tk()
		self.initDx = width
		self.initDy = height
		self.root.geometry( "%dx%d+50+30" % (self.initDx, self.initDy) )
		self.root.title("Strike Zone Visualization")
		self.root.maxsize( width, height )
		self.buildControls()
		self.images = [] #used to prevent our images from being garbage collected
		self.buildCanvas()
		self.root.lift()
		self.root.update_idletasks()
		self.setBindings()
		self.selected_point = None #holds the selected point to display info on rightcntlframe
		self.baseClick = None #used to keep track of mouse movement
		
		#fields relevant to strike zone analysis below
		
		#in our pitch mat list, the non-eject team will always be at the zero index
		#there will only ever be two pitch mats in the list at once (because we only have two strike zones):
		#non eject for the left strike zone, and eject for the right strike zone
		self.pitch_mats = []
		
		#all pitch mats, including the two not being displayed
		self.all_pitch_mats = []
		#list of miscall info for all pitch mats
		self.all_pitch_mats_miscall_info = []
		
		#list of miscall info for entire pitch mats from entire files
		#because previous ones are just focused on current random subset
		self.pitch_info_from_files = []
		
		#the x center point in pixels of the left and right averaged strike zones
		self.px_origins = []
		#the z (but is effectively the y) center point in pixels of the left and right averaged strike zones
		#note that pz refers to the pitch's height, this is a bit counter intuitive but he name of the data feature nonetheless
		self.pz_origins = []
		
		#list of the pitch canvas oval objects
		self.pitches = []
		#list of the strike zone canvas rectangle objects
		self.strikezones = []
		
		self.pixel_const = 100 # the pixel representation of 12 in. used for scaling pitch coords/strike zones
		
		#list of probabilities for both teams pre/post ejection of the four possible pitch outcomes
		self.bayes_info = []
		#list of anova results for both teams pre/post ejection
		self.anova_info = []
		#list of anova results for the ejection team
		self.anova_ejection_info = []
		
		self.random_subset_of_data()
		self.create_strikezones(self.pixel_const)
	
	def buildCanvas(self):
		self.canvas = tk.Canvas( self.root, width=self.initDx, height=self.initDy )
		self.canvas.pack( expand=tk.YES, fill=tk.BOTH )
		self.canvas.create_text(100,self.initDy-80,text="Green: actual ball called as strike\nYellow: actual strike called as ball")
		
		photoL = tk.PhotoImage(file="atbatleftie.gif")
		photoR = tk.PhotoImage(file="atbatrightie.gif")
		
		item = self.canvas.create_image(130,340, image=photoL)
		item = self.canvas.create_image(1070,340, image=photoR)
		
		self.images.append(photoL) #keep a reference so the image is not garbage collected
		self.images.append(photoR)		
		
		return
		
	def buildControls(self):
		bottomcntlframe = tk.Frame(self.root, height = 20, width = self.initDx)
		bottomcntlframe.pack(side=tk.BOTTOM)
		sep = tk.Frame( self.root, width=self.initDx, height=2, bd=1, relief=tk.SUNKEN )
		sep.pack(side=tk.BOTTOM)
		
		topcntlframe = tk.Frame(self.root, height = 20, width = self.initDx)
		topcntlframe.pack(side=tk.TOP)
		sep = tk.Frame( self.root, width=self.initDx, height=2, bd=1, relief=tk.SUNKEN )
		sep.pack(side=tk.TOP)
		
		self.left_error = tk.Label(topcntlframe, text = "", width = 20)
		self.left_error.pack(side=tk.LEFT)
		
		self.left_label = tk.Label(topcntlframe, text = "", width = 30)
		self.left_label.pack(side=tk.LEFT)
		
		self.right_error = tk.Label(topcntlframe, text = "", width = 20)
		self.right_error.pack(side=tk.RIGHT)
		
		self.right_label = tk.Label(topcntlframe, text = "", width = 30)
		self.right_label.pack(side=tk.RIGHT)
		
		#because we need to pass an argument to our method we will use lambda
		b = tk.Button(topcntlframe, text = "Pre Ejection", command= lambda: self.pre_or_post_ejection_pitches("pre"))
		b.pack(side = tk.LEFT)
		
		b = tk.Button(topcntlframe, text = "Post Ejection", command= lambda: self.pre_or_post_ejection_pitches("post"))
		b.pack(side = tk.LEFT)
		
		b = tk.Button(bottomcntlframe, text = "Show Miscalls", command=self.show_miscalls)
		b.pack(side = tk.LEFT, padx = 10)
		
		self.info_label = tk.Label(bottomcntlframe, text = "", width = 100)
		self.info_label.pack(side=tk.LEFT, padx = 20)
		
		b = tk.Button(bottomcntlframe, text = "Miscall Data", command=self.show_miscall_data)
		b.pack(side = tk.LEFT, padx = 10)
				
		return
	
	def setBindings(self):
		self.canvas.bind( '<Button-1>', self.select_pitch )
		self.root.bind( '<Command-q>', self.quit )
		self.root.bind( '<Command-c>', self.clear_pitches )
		
	def quit(self, event=None):
		self.root.destroy()
		
	def main(self):
		self.root.mainloop()
	
	def random_subset_of_data(self, num_rows = 1000):
		fn_list = ["preEjectPitchNonEjectTeam.csv", "preEjectPitchEjectTeam.csv",
				   "postEjectPitchNonEjectTeam.csv", "postEjectPitchEjectTeam.csv"]
		for fn in fn_list:
			d = data.Data(filename = fn)
			headers = d.get_headers()
			mat = d.get_data(headers)
			#get a random subset from the data
			rand_mat = np.matrix(np.zeros(shape=(num_rows,mat.shape[1])))
			counter = 0
			for i in range(num_rows):
				a = np.random.randint(0,mat.shape[0])
				rand_mat[counter,:] = mat[a,:]
				counter += 1
			
			if fn == "preEjectPitchNonEjectTeam.csv":
				self.pre_non_eject_team = np.matrix(rand_mat)
			elif fn == "preEjectPitchEjectTeam.csv":
				self.pre_eject_team = np.matrix(rand_mat)
			elif fn == "postEjectPitchNonEjectTeam.csv":
				self.post_non_eject_team = np.matrix(rand_mat)
			elif fn == "postEjectPitchEjectTeam.csv":
				self.post_eject_team = np.matrix(rand_mat)
			
		self.all_pitch_mats = [self.pre_non_eject_team, 
							   self.pre_eject_team,
							   self.post_non_eject_team,
							   self.post_eject_team]
			
		#data columns are
		#0	BatterHeight
		#1	PitchDescription
		#2	sz_top
		#3	sz_bot
		#4	px
		#5	pz
		#6	pz_norm
				
	def create_strikezones(self, pixel_const = 100):
		#sz width is always 17 in., pixel const is equivalent to a 12 in.
		sz_width = pixel_const*(17.0/12.0)
		for i in range(len(self.pitch_mats)):
			#same convention: the non eject teams are at the zero, on the left
			#and eject teams are at one, on the right
			sz_height = np.mean(self.pitch_mats[i][:,2]) - np.mean(self.pitch_mats[i][:,3])*pixel_const
			
			#if this is the left strike zone
			if i == 0:
				x_sz = ((self.initDx/2.0)-sz_width)/2.0
			elif i == 1:
				x_sz = ((self.initDx/2.0)-sz_width)/2.0+(self.initDx/2.0)
				
			y_sz = (self.initDy/2.0)-sz_height/2.0
			sz = self.canvas.create_rectangle(x_sz, y_sz, x_sz+sz_width, y_sz+sz_height)
			
			self.strikezones.append(sz)
			self.px_origins.append(x_sz + sz_width/2.0)
			self.pz_origins.append(y_sz + sz_height/2.0)
			
		divider = self.canvas.create_rectangle(self.initDx/2.0, 0,self.initDx/2.0,self.initDy)
	
	def pre_or_post_ejection_pitches(self, pre_or_post):
		self.clear_pitches()
		if pre_or_post == "pre":
			self.pitch_mats.append(self.pre_non_eject_team)
			self.pitch_mats.append(self.pre_eject_team)
			self.left_label['text'] = "NonEjection Team Pre Ejection"
			self.right_label['text'] = "Ejection Team Pre Ejection"
		elif pre_or_post == "post":	
			self.pitch_mats.append(self.post_non_eject_team)
			self.pitch_mats.append(self.post_eject_team)	
			self.left_label['text'] = "NonEjection Team Post Ejection"
			self.right_label['text'] = "Ejection Team Post Ejection"
		self.create_strikezones()
		self.plot_pitches()
	
	def plot_pitches(self, ball_width = 10):
		for i in range(len(self.pitch_mats)):
			#pitches sublist to be appended
			pitches = []
			for j in range(self.pitch_mats[i].shape[0]):
				pitches.append(self.canvas.create_oval(
					self.pitch_mats[i][j,4]*self.pixel_const + self.px_origins[i] - ball_width/2.0, 
					self.pitch_mats[i][j,6]*-1*self.pixel_const + self.pz_origins[i]- ball_width/2.0, 
					self.pitch_mats[i][j,4]*self.pixel_const + self.px_origins[i] + ball_width/2.0, 
					self.pitch_mats[i][j,6]*-1*self.pixel_const + self.pz_origins[i] + ball_width/2.0))
				if self.pitch_mats[i][j,1] == 1: 
					# A STRIKE	
					self.canvas.itemconfigure(pitches[j], fill = "red")
				elif self.pitch_mats[i][j,1] == 0: 
					# A BALL
					self.canvas.itemconfigure(pitches[j], fill = "deep sky blue")
			
			#append a sublist of the eject/non-eject pitches to pitches field
			self.pitches.append(pitches)
				
	def miscall_info(self):
		for i in range(len(self.all_pitch_mats)):
			info = [] #later appended to our attribute pitch info list
			
			#cb => called ball
			#ab => actual ball
			#cs => called strike
			#as => actual strike
			
			cs = 0
			ab_cs = 0
			cb = 0
			as_cb = 0
			all_pitches = float(self.all_pitch_mats[i].shape[0])
			
			for j in range(self.all_pitch_mats[i].shape[0]): 
				if self.all_pitch_mats[i][j,1] == 1: #if its a called strike
					cs += 1
					
					#if the pitch height is above the top of the strike zone
					#or if the pitch height is below the bottom of the strike zone 
					#or if the pitch's x coord is greater than half the width of the strikezone
					if (self.all_pitch_mats[i][j,5] > self.all_pitch_mats[i][j,2] or 
					self.all_pitch_mats[i][j,5] < self.all_pitch_mats[i][j,3] or 
					abs(self.all_pitch_mats[i][j,4]) > (17.0/12.0)/2.0):
						ab_cs += 1
				
				elif self.all_pitch_mats[i][j,1] == 0: #if its a called ball
					cb += 1
					
					#if the pitch height is below the top of the strike zone
					#and if the pitch height is above the bottom of the strike zone 
					#and if the pitch's x coord is less than half the width of the strikezone
					if (self.all_pitch_mats[i][j,5] < self.all_pitch_mats[i][j,2] and 
					self.all_pitch_mats[i][j,5] > self.all_pitch_mats[i][j,3] and 
					abs(self.all_pitch_mats[i][j,4]) < (17.0/12.0)/2.0):
						as_cb += 1
							
			info.append(ab_cs / float(cs))
			info.append(as_cb / float(cb))
			total_miscalls = (ab_cs + as_cb) / all_pitches
			info.append(total_miscalls)
			
			self.all_pitch_mats_miscall_info.append(info)
			
			#sublist order: 
			#0 	%of all called strikes that were actually balls
			#1	%of all called balls that were actually strikes
			#2	%of all pitches that were miscalled
			
		#additionally, let's read in our entire datasets (the same calculations but using
		#all of the pitches we have data for, extending beyond these current randomly
		#selected subsets that we've used simply for visualization processes)
		self.pitch_info_from_files = strikeZoneAnalysis.miscall_info()
		
		#additional lists of information based on entire dataset for our subsequent analyses dialog boxes
		self.bayes_info = strikeZoneAnalysis.bayes_probabilities()			   
		self.anova_info = strikeZoneAnalysis.anova1()
		self.anova_ejection_info = strikeZoneAnalysis.anova1(["preEjectPitchEjectTeam.csv", "postEjectPitchEjectTeam.csv"])
	
	def show_miscalls(self):
		for i in range(len(self.pitch_mats)):
			actual_balls_called_as_strikes = 0.0
			actual_strikes_called_as_balls = 0.0
			for j in range(self.pitch_mats[i].shape[0]): 
				if self.pitch_mats[i][j,1] == 1: #if its a called strike
					#if the pitch height is above the top of the strike zone
					#or if the pitch height is below the bottom of the strike zone 
					#or if the pitch's x coord is greater than half the width of the strikezone
					if (self.pitch_mats[i][j,5] > self.pitch_mats[i][j,2] or 
					self.pitch_mats[i][j,5] < self.pitch_mats[i][j,3] or 
					abs(self.pitch_mats[i][j,4]) > (17.0/12.0)/2.0):
						actual_balls_called_as_strikes += 1.0
						self.canvas.itemconfigure(self.pitches[i][j], fill = "green")
				elif self.pitch_mats[i][j,1] == 0: #if its a called ball
					#if the pitch height is below the top of the strike zone
					#and if the pitch height is above the bottom of the strike zone 
					#and if the pitch's x coord is less than half the width of the strikezone
					if (self.pitch_mats[i][j,5] < self.pitch_mats[i][j,2] and 
					self.pitch_mats[i][j,5] > self.pitch_mats[i][j,3] and 
					abs(self.pitch_mats[i][j,4]) < (17.0/12.0)/2.0):
						actual_strikes_called_as_balls += 1.0
						self.canvas.itemconfigure(self.pitches[i][j], fill = "yellow")
					
			if i == 0:
				self.left_error['text'] = str(round((((actual_balls_called_as_strikes + actual_strikes_called_as_balls) / self.pitch_mats[i].shape[0] ) * 100.0), 4)) + "% miscalls"
			elif i == 1:
				self.right_error['text'] = str(round((((actual_balls_called_as_strikes + actual_strikes_called_as_balls) / self.pitch_mats[i].shape[0] ) * 100.0), 4)) + "% miscalls"
		
	def show_miscall_data(self):
		#since we are about to display miscall info, if we have not yet
		#computed the info (ie this is the first time the button is being pressed)
		#then do so now
		if len(self.all_pitch_mats_miscall_info) == 0:
			 self.miscall_info()
		data_box = miscall_data_box(self.root, title = "Miscall Info")
	
	def clear_pitches(self, event=None):
		for i in range(len(self.pitches)):
			self.canvas.delete(self.strikezones[i])
			for pitch in self.pitches[i]:
				self.canvas.delete(pitch)
		self.left_error['text'] = ""
		self.right_error['text'] = ""
		self.strikezones = []
		self.pitch_mats = []
		self.pitches = []

	def select_pitch(self, event):
		self.baseClick = (event.x, event.y)
	
		for i in range(len(self.pitches)):
			for j in range(len(self.pitches[i])):
				location = self.canvas.coords(self.pitches[i][j])
				if (self.baseClick[0] > location[0] and self.baseClick[0] < location[2] and self.baseClick[1] > location[1] and self.baseClick[1] < location[3]):
					#if we got here we have selected a point
					#if we previously had a point selected lets unselect it
					if self.selected_point != None:
						self.canvas.itemconfigure(self.pitches[self.selected_point[0]][self.selected_point[1]], width = 1)
					self.selected_point = (i,j)
					self.canvas.itemconfigure(self.pitches[i][j], width = 3)
					
					info_string = ""
					mat_row = self.pitch_mats[i][j,:]
					info_string += "batter height: " + str(self.pitch_mats[i][j,0]) + "   "
					if self.pitch_mats[i][j,1] == 1.0:
						info_string += "called: strike" + "   "
					elif self.pitch_mats[i][j,1] == 0.0:
						info_string += "called: ball" + "   "
					info_string += "strikezone top: " + str(self.pitch_mats[i][j,2]) + "   "
					info_string += "strikezone bottom: " + str(self.pitch_mats[i][j,3])  + "   "
					info_string += "px: " + str(self.pitch_mats[i][j,4]) + "   " 
					info_string += "pz: " + str(self.pitch_mats[i][j,5]) + "   "
					
					self.info_label['text'] = info_string
					return
				else:
					if self.selected_point != None:
						self.canvas.itemconfigure(self.pitches[self.selected_point[0]][self.selected_point[1]], width = 1)
					self.info_label['text'] = "no pitch selected"

class Dialog(tk.Toplevel):
	def __init__(self, parent = DisplayApp, title = None):
		tk.Toplevel.__init__(self, parent)
		self.transient(parent)

		if title:
			self.title(title)

		self.parent = parent
		self.result = None
		body = tk.Frame(self)
		self.initial_focus = self.body(body)
		body.pack(padx=5, pady=5)
		self.buttonbox()
		self.grab_set()

		if not self.initial_focus:
			self.initial_focus = self

		self.protocol("WM_DELETE_WINDOW", self.cancel)
		self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
								  parent.winfo_rooty()+50))
		self.initial_focus.focus_set()
		self.wait_window(self)

	# construction hooks
	def body(self, master):
		# create dialog body.  return widget that should have
		# initial focus.  this method should be overridden
		pass

	def buttonbox(self):
		# add standard button box. override if you don't want the
		# standard buttons
		box = tk.Frame(self)

		w = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
		w.pack(side=tk.LEFT, padx=5, pady=5)
		w = tk.Button(box, text="Cancel", width=10, command=self.cancel)
		w.pack(side=tk.LEFT, padx=5, pady=5)

		self.bind("<Return>", self.ok)
		self.bind("<Escape>", self.cancel)
		box.pack()

	# standard button semantics
	def ok(self, event=None):
		self.withdraw()
		self.update_idletasks()

		self.apply()
		self.parent.focus_set()
		self.destroy()

	def cancel(self, event=None):
		# put focus back to the parent window
		self.parent.focus_set()
		self.destroy()

	# command hooks
	def validate(self):
		return 1 # override

	def apply(self):
		pass # override

class miscall_data_box(Dialog):
	'''Creates a child class of the dialog box to choose random distributions'''
	def body(self, master):
		'''Adds list boxes to the body of dialog window'''
		tk.Label(master, text="NonEjection Team", anchor= tk.W).grid(row=0, column=0, sticky = tk.W)
		tk.Label(master, text="     ").grid(row=0, column=1)
		tk.Label(master, text="Ejection Team").grid(row=0, column=2, sticky = tk.W)
		
		tk.Label(master, text="Pre Ejection").grid(row=1, column=0, sticky = tk.W)
		tk.Label(master, text="Pre Ejection").grid(row=1, column=2, sticky = tk.W)
		
		info = dapp.all_pitch_mats_miscall_info
		for i in range(4):
			if i == 0 or i == 1:
				row_count = 2
			elif i == 2 or i == 3:
				row_count = 6
			if i == 0 or i == 2:
				col = 0
			if i == 1 or i == 3:
				col = 2
			txt = "\tActual balls called as strikes: " + "%s"%np.around(info[i][0]*100.0,3) + "%"
			tk.Label(master, text=txt).grid(row=row_count, column=col, sticky=tk.W)
			txt = "\tActual strikes called as balls: " + "%s"%np.around(info[i][1]*100.0,3) + "%"
			tk.Label(master, text=txt).grid(row=row_count+1, column=col, sticky=tk.W)
			txt = "\tTotal miscalls: " + "%s"%np.around(info[i][2]*100.0,3) + "%"
			tk.Label(master, text=txt).grid(row=row_count+2, column=col, sticky=tk.W)
			
			if i == 0 or i == 1:
				tk.Label(master, text="Post Ejection").grid(row=row_count+3, column=col, sticky = tk.W)
		return
	
	def buttonbox(self):
		# add standard button box. override if you don't want the
		# standard buttons
		box = tk.Frame(self)

		w = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
		w.pack(side=tk.LEFT, padx=5, pady=5)
		w = tk.Button(box, text="Miscall Data From Entire Files", width=30, command=self.open_next_d_box)
		w.pack(side=tk.LEFT, padx=5, pady=5)

		self.bind("<Return>", self.ok)
		box.pack()
		
	def open_next_d_box(self, event=None):
		# put focus back to the parent window
		self.parent.focus_set()
		self.destroy()
		#open the corresponding window
		data_box = miscall_data_box_all_data_from_files(dapp.root, title = "Miscall Data From Entire Files")
		
class miscall_data_box_all_data_from_files(Dialog):
	'''Creates a child class of the dialog box to choose random distributions'''
	def body(self, master):
		'''Adds list boxes to the body of dialog window'''
		tk.Label(master, text="NonEjection Team", anchor= tk.W).grid(row=0, column=0, sticky = tk.W)
		tk.Label(master, text="     ").grid(row=0, column=1)
		tk.Label(master, text="Ejection Team").grid(row=0, column=2, sticky = tk.W)
		
		tk.Label(master, text="Pre Ejection").grid(row=1, column=0, sticky = tk.W)
		tk.Label(master, text="Pre Ejection").grid(row=1, column=2, sticky = tk.W)
		
		info = dapp.pitch_info_from_files
		for i in range(4):
			if i == 0 or i == 1:
				row_count = 2
			elif i == 2 or i == 3:
				row_count = 6
			if i == 0 or i == 2:
				col = 0
			if i == 1 or i == 3:
				col = 2
			txt = "\tActual balls called as strikes: " + "%s"%np.around(info[i][0]*100.0,3) + "%"
			tk.Label(master, text=txt).grid(row=row_count, column=col, sticky=tk.W)
			txt = "\tActual strikes called as balls: " + "%s"%np.around(info[i][1]*100.0,3) + "%"
			tk.Label(master, text=txt).grid(row=row_count+1, column=col, sticky=tk.W)
			txt = "\tTotal miscalls: " + "%s"%np.around(info[i][2]*100.0,3) + "%"
			tk.Label(master, text=txt).grid(row=row_count+2, column=col, sticky=tk.W)
			
			if i == 0 or i == 1:
				tk.Label(master, text="Post Ejection").grid(row=row_count+3, column=col, sticky = tk.W)
		return
		
	def buttonbox(self):
		# add standard button box. override if you don't want the
		# standard buttons
		box = tk.Frame(self)

		w = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
		w.pack(side=tk.LEFT, padx=5, pady=5)
		w = tk.Button(box, text="Bayes & ANOVA Analysis", width=30, command=self.open_next_d_box)
		w.pack(side=tk.LEFT, padx=5, pady=5)

		self.bind("<Return>", self.ok)
		box.pack()
		
	def open_next_d_box(self, event=None):
		# put focus back to the parent window
		self.parent.focus_set()
		self.destroy()
		#open the corresponding window
		data_box = bayes_data_box(dapp.root, title = "Bayes Analysis")
		
class bayes_data_box(Dialog):
	'''Creates a child class of the dialog box to choose random distributions'''
	def body(self, master):
		'''Adds list boxes to the body of dialog window'''
		tk.Label(master, text="NonEjection Team", anchor= tk.W).grid(row=0, column=0, sticky = tk.W)
		tk.Label(master, text="     ").grid(row=0, column=1)
		tk.Label(master, text="Ejection Team").grid(row=0, column=2, sticky = tk.W)
		
		tk.Label(master, text="Pre Ejection").grid(row=1, column=0, sticky = tk.W)
		tk.Label(master, text="Pre Ejection").grid(row=1, column=2, sticky = tk.W)
		
		info = dapp.bayes_info
		
		for i in range(4):
			if i == 0 or i == 1:
				row_count = 2
			elif i == 2 or i == 3:
				row_count = 8
			if i == 0 or i == 2:
				col = 0
			if i == 1 or i == 3:
				col = 2
			txt = "\tProbability of a called strike being an actual strike: " + "%s"%np.around(info[i][0]*100.0,3) + "%"
			tk.Label(master, text=txt).grid(row=row_count, column=col, sticky=tk.W)
			txt = "\tProbability of a called strike being an actual ball: " + "%s"%np.around(info[i][1]*100.0,3) + "%"
			tk.Label(master, text=txt).grid(row=row_count+1, column=col, sticky=tk.W)
			txt = "\tProbability of a called ball being an actual ball: " + "%s"%np.around(info[i][2]*100.0,3) + "%"
			tk.Label(master, text=txt).grid(row=row_count+2, column=col, sticky=tk.W)
			txt = "\tProbability of a called ball being an actual strike: " + "%s"%np.around(info[i][3]*100.0,3) + "%"
			tk.Label(master, text=txt).grid(row=row_count+3, column=col, sticky=tk.W)
			
			if i == 0 or i == 1:
				tk.Label(master, text="Post Ejection").grid(row=row_count+4, column=col, sticky = tk.W)
		
		return
		
	def buttonbox(self):
		# add standard button box. override if you don't want the
		# standard buttons
		box = tk.Frame(self)

		w = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
		w.pack(side=tk.LEFT, padx=5, pady=5)
		w = tk.Button(box, text="ANOVA Analysis", width=30, command=self.open_next_d_box)
		w.pack(side=tk.LEFT, padx=5, pady=5)
		
		self.bind("<Return>", self.ok)
		box.pack()
		
	def open_next_d_box(self, event=None):
		# put focus back to the parent window
		self.parent.focus_set()
		self.destroy()
		#open the corresponding window
		data_box = anova_data_box(dapp.root, title = "ANOVA Analysis")

class anova_data_box(Dialog):
	'''Creates a child class of the dialog box to choose random distributions'''
	def body(self, master):
		'''Adds list boxes to the body of dialog window'''
		tk.Label(master, text="ANOVA Table\n(computed for called\nstrikes that were \nactually balls within all\nfour team conditions)", 
			     anchor= tk.W).grid(row=0, column=0, sticky = tk.W)
		tk.Label(master, text="Sum of Squares  ").grid(row=1, column=1, sticky = tk.W)
		tk.Label(master, text="Degrees of Freedom  ").grid(row=1, column=2, sticky = tk.W)
		tk.Label(master, text="Mean Squared  ").grid(row=1, column=3, sticky = tk.W)
		tk.Label(master, text="F").grid(row=1, column=4, sticky = tk.W)
		tk.Label(master, text="\tCritical value of F").grid(row=1, column=5, sticky = tk.W)
		
		tk.Label(master, text="Between").grid(row=2, column=0, sticky = tk.W)
		tk.Label(master, text="Within").grid(row=3, column=0, sticky = tk.W)
		tk.Label(master, text="Total").grid(row=4, column=0, sticky = tk.W)
		
		info = dapp.anova_info
		for i in range(len(info)):
			#because of the uneven sublist lengths
			if i <= 2:
				txt = "%s"%np.around(info[i][0],3)
				tk.Label(master, text=txt).grid(row=2+i, column=1, sticky=tk.W)
				txt = "%s"%np.around(info[i][1],3)
				tk.Label(master, text=txt).grid(row=2+i, column=2, sticky=tk.W)
			if i <= 1:
				txt = "%s"%np.around(info[i][2],3)
				tk.Label(master, text=txt).grid(row=2+i, column=3, sticky=tk.W)
			if i <= 0:
				txt = "%s"%np.around(info[i][3],3)
				tk.Label(master, text=txt).grid(row=2+i, column=4, sticky=tk.W)
				txt = "\t%s"%np.around(info[i][4],3)
				tk.Label(master, text=txt).grid(row=2+i, column=5, sticky=tk.W)
				
		tk.Label(master, text="").grid(row=5, column=0, sticky=tk.W)
		txt = "The four conditions\ndiffered significantly\nF(%s"%info[0][1]
		txt += ",%s"%info[1][1]
		txt += ") = %s"%np.around(info[0][3],3)
		txt += ",\np < 0.05"
		tk.Label(master, text=txt).grid(row=6, column=0, sticky=tk.W)
		
		return
		
	def buttonbox(self):
			# add standard button box. override if you don't want the
			# standard buttons
			box = tk.Frame(self)

			w = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
			w.pack(side=tk.LEFT, padx=5, pady=5)
			w = tk.Button(box, text="ANOVA Analysis Ejection Teams", width=30, command=self.open_next_d_box)
			w.pack(side=tk.LEFT, padx=5, pady=5)
		
			self.bind("<Return>", self.ok)
			box.pack()
		
	def open_next_d_box(self, event=None):
		# put focus back to the parent window
		self.parent.focus_set()
		self.destroy()
		#open the corresponding window
		data_box = anova_ejection_team_data_box(dapp.root, title = "ANOVA Analysis Ejection Teams")
		
class anova_ejection_team_data_box(Dialog):
	'''Creates a child class of the dialog box to choose random distributions'''
	def body(self, master):
		'''Adds list boxes to the body of dialog window'''
		tk.Label(master, text="ANOVA Table\n(computed for called\nstrikes that were \nactually balls between\npre & post ejection\nfor the ejection team)", 
				 anchor= tk.W).grid(row=0, column=0, sticky = tk.W)
		tk.Label(master, text="Sum of Squares  ").grid(row=1, column=1, sticky = tk.W)
		tk.Label(master, text="Degrees of Freedom  ").grid(row=1, column=2, sticky = tk.W)
		tk.Label(master, text="Mean Squared  ").grid(row=1, column=3, sticky = tk.W)
		tk.Label(master, text="F").grid(row=1, column=4, sticky = tk.W)
		tk.Label(master, text="\tCritical value of F").grid(row=1, column=5, sticky = tk.W)
		
		tk.Label(master, text="Between").grid(row=2, column=0, sticky = tk.W)
		tk.Label(master, text="Within").grid(row=3, column=0, sticky = tk.W)
		tk.Label(master, text="Total").grid(row=4, column=0, sticky = tk.W)
		
		info = dapp.anova_ejection_info
		for i in range(len(info)):
			#because of the uneven sublist lengths
			if i <= 2:
				txt = "%s"%np.around(info[i][0],3)
				tk.Label(master, text=txt).grid(row=2+i, column=1, sticky=tk.W)
				txt = "%s"%np.around(info[i][1],3)
				tk.Label(master, text=txt).grid(row=2+i, column=2, sticky=tk.W)
			if i <= 1:
				txt = "%s"%np.around(info[i][2],3)
				tk.Label(master, text=txt).grid(row=2+i, column=3, sticky=tk.W)
			if i <= 0:
				txt = "%s"%np.around(info[i][3],3)
				tk.Label(master, text=txt).grid(row=2+i, column=4, sticky=tk.W)
				txt = "\t%s"%np.around(info[i][4],3)
				tk.Label(master, text=txt).grid(row=2+i, column=5, sticky=tk.W)
				
		tk.Label(master, text="").grid(row=5, column=0, sticky=tk.W)
		txt = "The two conditions\ndiffered significantly\nF(%s"%info[0][1]
		txt += ",%s"%info[1][1]
		txt += ") = %s"%np.around(info[0][3],3)
		txt += ",\np < 0.05"
		tk.Label(master, text=txt).grid(row=6, column=0, sticky=tk.W)
		
		return

if __name__ == "__main__":
	dapp = DisplayApp(1200, 700)
	dapp.main()