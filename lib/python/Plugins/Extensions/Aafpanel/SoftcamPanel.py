from Components.config import config, ConfigSubsection, ConfigText
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.MenuList import MenuList
from Components.Label import Label
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from enigma import *
import os

def command(comandline, strip=1):
  comandline = comandline + " >/tmp/command.txt"
  os.system(comandline)
  text = ""
  if os.path.exists("/tmp/command.txt") is True:
    file = open("/tmp/command.txt", "r")
    if strip == 1:
      for line in file:
        text = text + line.strip() + '\n'
    else:
      for line in file:
        text = text + line
        if text[-1:] != '\n': text = text + "\n"
    file.close
  # if one or last line then remove linefeed
  if text[-1:] == '\n': text = text[:-1]
  comandline = text
  os.system("rm /tmp/command.txt")
  return comandline

class EMUlist(MenuList):
	def __init__(self, list=[], enableWrapAround = False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		Schriftart = 22
		self.l.setFont(0, gFont("Regular", Schriftart))
		self.l.setItemHeight(24)

	def moveSelection(self,idx=0):
		if self.instance is not None:
			self.instance.moveSelectionTo(idx)

SOFTCAM_SKIN = """<screen name="SoftcamPanel" position="center,center" size="500,450" title="Softcam Panel">
	<eLabel font="Regular;22" position="10,10" size="185,25" text="Softcam Selection:" />
	<widget font="Regular;18" name="camcount" position="420,10" size="60,25" />
	<widget name="Mlist" position="200,10" size="200,25" />
	<widget font="Regular;22" name="enigma2" position="10,10" size="185,25" />
	<eLabel backgroundColor="red" position="10,60" size="120,3" zPosition="0" />
	<eLabel backgroundColor="green" position="130,60" size="120,3" zPosition="0" />
	<eLabel backgroundColor="yellow" position="250,60" size="120,3" zPosition="0" />
	<eLabel backgroundColor="blue" position="370,60" size="120,3" zPosition="0" />
	<widget font="Regular;16" halign="center" name="key_red" position="10,62" size="120,35" transparent="1" valign="center" zPosition="2" />
	<widget font="Regular;16" halign="center" name="key_green" position="130,62" size="120,35" transparent="1" valign="center" zPosition="2" />
	<widget font="Regular;16" halign="center" name="key_yellow" position="250,62" size="120,35" transparent="1" valign="center" zPosition="2" />
	<widget font="Regular;16" halign="center" name="key_blue" position="370,62" size="120,35" transparent="1" valign="center" zPosition="2" />
	<eLabel backgroundColor="#56C856" position="0,99" size="500,1" zPosition="0" />
	<widget font="Regular;22" name="actifcam" position="10,100" size="480,32" />
	<eLabel backgroundColor="#56C856" position="0,133" size="500,1" zPosition="0" />
	<widget font="Regular;16" name="ecminfo" position="10,140" size="480,300" />
	<widget name="emulist" position="160,160" size="190,245" scrollbarMode="showOnDemand" />
</screen>"""

config.softcam = ConfigSubsection()
config.softcam.actCam = ConfigText(visible_width = 200)

class SoftcamPanel(Screen):
	def __init__(self, session):
		global emuDir
		emuDir = "/etc/"
		self.service = None
		Screen.__init__(self, session)

		self.skin = SOFTCAM_SKIN
		self.onShown.append(self.setWindowTitle)

		self.mlist = []
		self["Mlist"] = MenuList(self.mlist)
		#// set the label text
		self["key_green"] = Label(_("Restart"))
		self["key_red"] = Label(_("Stop"))
		self["key_yellow"] = Label(_("Refresh"))
		self["key_blue"]= Label(_("Exit"))
		self["ecminfo"] = Label(_("No ECM info"))
		self["camcount"] = Label("(0/0)")
		self["actifcam"] = Label(_("no CAM active"))
		self["enigma2"] = Label("")
		self["emulist"] = EMUlist([0,(eListboxPythonMultiContent.TYPE_TEXT, 0, 0,250, 30, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, "EMU not found")])

		#// create listings
		self.emuDirlist = []
		self.emuList = []
		self.emuBin = []
		self.emuStart = []
		self.emuStop = []
		self.emuRgui = []
		self.emuDirlist = os.listdir(emuDir)
		self.ecmtel = 0
		self.first = 0
		global count
		count = 0
		#// check emu dir for config files
		print "************ go in the emuloop ************"
		for x in self.emuDirlist:
			#// if file contains the string "emu" (then this is a emu config file)
			if x.find("emu") > -1:
				self.emuList.append(emuDir + x)
				em = open(emuDir + x)
				self.emuRgui.append(0)
				#// read the emu config file
				for line in em.readlines():
					line1 = line
					#// emuname
					line = line1
					if line.find("startcam") > -1:
						line = line.split("=")
						self.emuStart.append(line[1].strip())
						print  '[SOFTCAM] startcam: ' + line[1].strip()

					#// stopcam
					line = line1
					if line.find("stopcam") > -1:
						line = line.split("=")
						self.emuStop.append(line[1].strip())
						print  '[SOFTCAM] stopcam: ' + line[1].strip()

					#// Restart GUI
					line = line1
					if line.find("restartgui") > -1:
						self.emuRgui[count] = 1
						print  '[SOFTCAM] emuname: ' + line[1].strip()

					#// binname
					line = line1
					if line.find("binname") > -1:
						line = line.split("=")
						self.emuBin.append(line[1].strip())
						print  '[SOFTCAM] binname: ' + line[1].strip()
					#// startcam
				em.close()
				count += 1
				self["camcount"].setText("(1/" + str(count) + ")")

		self.maxcount = count
		self.ReadMenu()

		self["emulist"].hide()
		self["Mlist"].show()
		self["ecminfo"].show()
		self.focus = "ml"

		self.read_shareinfo()
		self.Timer = eTimer()
		self.Timer.callback.append(self.layoutFinished)
		self.Timer.start(2000, True)
		#// get the remote buttons
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions"],
		{
			"cancel": self.Exit,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
			"ok": self.ok,
			"blue": self.Exit,
			"red": self.Red,
			"green": self.Green,
			"yellow": self.Yellow,
		}, -1)
		#// update screen
		self.onLayoutFinish.append(self.layoutFinished)

	def setWindowTitle(self):
		self.setTitle(_("Softcam Panel V1.0"))

	def ReadMenu(self):
		self.whichCam()
		self.fileresultlist = []
		for x in self.emuDirlist:
			#// if file contains the string "emu" (then this is a emu config file)
			if x.find("emu") > -1:
				self.emuList.append(emuDir + x)
				em = open(emuDir + x)
				self.emuRgui.append(0)
				#// read the emu config file
				for line in em.readlines():
					farbwahl = 16777215  # weiss
					line1 = line
					#// emuname
					line = line1
					if line.find("emuname") > -1:
						line = line.split("=")
						self.mlist.append(line[1].strip())
						name = line[1].strip()
						print "current CAM" + self.curcam
						if self.curcam == name:
							farbwahl = 65280  # print in green
						entry = [[name],(eListboxPythonMultiContent.TYPE_TEXT, 0, 0,250, 30, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, name, farbwahl)]
						print "adding to feedlist: " + str(entry), farbwahl
						self.fileresultlist.append(entry)
				em.close()
		self["emulist"].l.setList(self.fileresultlist)
		camIndex = self["Mlist"].getSelectedIndex()
		self["emulist"].moveSelection(0)

	def whichCam(self):
			#// check for active cam
			self.curcam = ""
			for x in self.emuBin:
				p = command('pidof ' + x + ' |wc -w')
				if not p.isdigit(): p=0
				if int(p) > 0:
					self.curcam = x
					break

	def layoutFinished(self):
		self.Timer.stop()
		#// check for active cam
		try:
			global oldcamIndex
			oldcamIndex = 0
			tel = 0
			camrunning = 0
			for x in self.emuBin:
				print '[SOFTCAM] searching active cam: ' + x
				p = command('pidof ' + x + ' |wc -w')
				if not p.isdigit(): p=0
				if int(p) > 0:
					oldcamIndex = tel
					if self.first == 0: # Only update first time or when refresh button was pressed
						self["Mlist"].moveToIndex(tel)
						self["emulist"].moveToIndex(tel)
						actcam = self.mlist[tel]

					self["camcount"].setText("(" + str(tel + 1) + "/" + str(count) + ")")
					self["key_green"].setText(_("Restart"))
					self.Save_Settings(actcam)
					self["actifcam"].setText(_("active CAM: ") + actcam )
					print  '[SOFTCAM] set active cam to: ' + actcam
					self.Label_restart_Enigma2(tel)
					camrunning = 1
					break
				else:
					tel +=1
			#// CAM IS NOT RUNNING
			if camrunning == 0:
				actcam = _("no CAM active")
				self["actifcam"].setText(actcam )
				self["key_green"].setText(_("Start"))
				if os.path.exists('/tmp/ecm.info') is True:
					os.system("rm /tmp/ecm.info")
				if os.path.exists('/tmp/ecm0.info') is True:
					os.system("rm /tmp/ecm0.info")
				self.Save_Settings(actcam)
				self.Label_restart_Enigma2(tel)
			self.first = 1
		except:
			pass

		#// read ecm.info
		ecmi = ""
		if os.path.exists('/tmp/ecm.info') is True:
			ecmi = self.read_ecm('/tmp/ecm.info')
		elif os.path.exists('/tmp/ecm1.info') is True:
			ecmi = self.read_ecm('/tmp/ecm1.info')
		else:
			ecmi = _("No ECM info")
		ecmold = self["ecminfo"].getText()
		if ecmold == ecmi:
			self.ecmtel += 1
			if self.ecmtel > 5:
				ecmi = _("No new ECM info")
		else:
			self.ecmtel = 0
		self["ecminfo"].setText(ecmi)
		self.Timer.start(2000, True)		#reset timer

	def read_shareinfo(self):
		#// read share.info and put in list
		self.shareinfo =[]
		if os.path.exists('/tmp/share.info') is True:
			s = open('/tmp/share.info')
			for x in s.readlines():
				self.shareinfo.append(x)
			s.close()

	def read_ecm(self, ecmpath):
		#// read ecm.info and check for share.info
		ecmi2 = ''
		Caid = ''
		Prov = ''
		f = open(ecmpath)
		for line in f.readlines():
			line= line.replace('=', '')
			line= line.replace(' ', '', 1)
			#// search CaID
			if line.find('ECM on CaID') > -1:
				k = line.find('ECM on CaID') + 14
				Caid = line[k:k+4]
			#// search Boxid
			if line.find('prov:') > -1:
				tmpprov = line.split(':')
				Prov = tmpprov[1].strip()
				#// search peer in share.info only if share.info exists
				if Caid <> '' and Prov <> '' and len(self.shareinfo) > 0 :
					for x in self.shareinfo:
						cel = x.split(' ')
						#// search Boxid and Caid
						if cel[5][0:4] == Caid and cel[9][3:7] == Prov:
							line = 'Peer: ' + Prov + ' - ' + cel[3] + ' - ' + cel[8] + '\n'
							break
			ecmi2 = ecmi2 + line
		f.close()
		return ecmi2

	def up(self):
		print "you pressed up"
		self.Timer.stop()
		self["emulist"].show()
		self["Mlist"].hide()
		self["ecminfo"].hide()
		self.focus = "em"
		print "Count=" + str(count)
		curentIndex = self["Mlist"].getSelectedIndex()
		print "CurentIndex=" + str(curentIndex)
		if count > 0 and curentIndex >0:
			self["emulist"].up()
			self["Mlist"].up()
			camIndex = self["Mlist"].getSelectedIndex()
			#camIndex = self["emulist"].getSelectedIndex()
			self["camcount"].setText("(" + str(camIndex + 1 )+ "/" + str(count) + ")")
			self.Label_restart_Enigma2(camIndex)

	def down(self):
		print "you pressed down"
		self.Timer.stop()
		self["emulist"].show()
		self["Mlist"].hide()
		self["ecminfo"].hide()
		self.focus = "em"
		print "Count=" + str(count)
		curentIndex = self["Mlist"].getSelectedIndex()
		if count > 0 and (curentIndex + 1)  < count:
			self["emulist"].down()
			self["Mlist"].down()
			camIndex = self["Mlist"].getSelectedIndex()
			#camIndex = self["emulist"].getSelectedIndex()
			self["camcount"].setText("(" + str(camIndex + 1 )+ "/" + str(count) + ")")
			self.Label_restart_Enigma2(camIndex)

	def ShowEmuList(self):
		self["emulist"].hide()
		self["Mlist"].show()
		self["ecminfo"].show()
		self.focus = "ml"

	def Red(self):
		#// Stopping the CAM when pressing the RED button
		self.Timer.stop()
		self.Stopcam()
		self.Timer.start(2000, True)		#reset timer

	def Yellow(self):
		self.ShowEmuList()
		self.first = 0
		self.layoutFinished()

	def Green(self):
		#// Start the CAM when pressing the GREEN button
		self.ShowEmuList()
		self.Timer.stop()
		self.Startcam()
		self.Timer.start(2000, True)		#reset timer


	def left(self):
		#// Go to the previous CAM in list
		self["emulist"].hide()
		self["Mlist"].show()
		self["ecminfo"].show()
		self.focus = "ml"
		curentIndex = self["Mlist"].getSelectedIndex()
		if count > 0 and curentIndex >0:
			global camIndex
			self["Mlist"].up()
			self["emulist"].up()
			camIndex = self["Mlist"].getSelectedIndex()
			self["camcount"].setText("(" + str(camIndex + 1 )+ "/" + str(count) + ")")
			self.Label_restart_Enigma2(camIndex)

	def right(self):
		#// Go to the next CAM in list
		self["emulist"].hide()
		self["Mlist"].show()
		self["ecminfo"].show()
		self.focus = "ml" # which list is active
		curentIndex = self["Mlist"].getSelectedIndex()
		if count > 0 and (curentIndex + 1)  < count:
			global camIndex
			self["Mlist"].down()
			self["emulist"].down()
			camIndex = self["Mlist"].getSelectedIndex()
			#	camIndex = self["Mlist"].getSelectedIndex()
			self["camcount"].setText("(" + str(camIndex + 1 )+ "/" + str(count) + ")")
			self.Label_restart_Enigma2(camIndex)

	def Exit(self):
		self.Timer.stop()
		self.close()

	def ok(self):
		#// Exit Softcam when pressing the OK button
		self.ShowEmuList()
		self.Timer.stop()
		self.Startcam()
		self.Yellow()
		self.Timer.start(2000, True)		#reset timer

	def Stopcam(self):
		#// Stopping the CAM
		self.ShowEmuList()
		global oldcamIndex
		oldcam = self.emuBin[oldcamIndex]
		print  '[SOFTCAM] stop cam: ' + oldcam
		self.container = eConsoleAppContainer()
		self.container.execute(self.emuStop[oldcamIndex])
		if os.path.exists('/tmp/ecm.info') is True:
			os.system("rm /tmp/ecm.info")
		# check if incubus_watch runs
		p = command('pidof incubus_watch |wc -w')
		if not p.isdigit(): p=0
		if int(p) > 0:
			# stop incubus_watch
			print '[SOFTCAM] stop incubus_watch'
			self.container = eConsoleAppContainer()
			self.container.execute('killall -9 incubus_watch')
		import time
		time.sleep(1) # was 5sec
		t = 0
		while t < 5:
			p = command('pidof %s |wc -w' % oldcam )
			if not p.isdigit(): p=0
			if int(p) > 0:
				self.container = eConsoleAppContainer()
				self.container.execute('killall -9 ' + oldcam)
				t += 1
				time.sleep(1)
			else:
				t = 5
		actcam = _("no CAM active")
		self["actifcam"].setText(actcam)
		self["key_green"].setText(_("Start"))
		self["ecminfo"].setText(_("No ECM info"))
		self.Save_Settings(actcam)

	def Startcam(self):
		#// Starting the CAM
		print "count=",count
		try:
			if count > 0:
				self.Stopcam()
				global camIndex
				camIndex = self["Mlist"].getSelectedIndex()
				print "camindex", camIndex
				actcam = self.mlist[camIndex]
				print  '[SOFTCAM ml] start cam: ' + actcam
				self["actifcam"].setText(_("active CAM: ") + actcam)
				emustart = self.emuStart[camIndex][self.emuStart[camIndex].find(self.emuBin[camIndex]):]
				print emustart
				self.Save_Settings(actcam)
				start = self.emuStart[camIndex]
				import time
				time.sleep (1) # was 5sec
				if self.emuRgui[camIndex] == 0:
					kk = start.find(';')
					if kk >-1:
						print "[SOFTCAM] starting two cam's"
						emu1 = start[0:kk]
						emu2 = start[kk+1:]
						print "[SOFTCAM] starting cam 1 " + emu1
						self.container = eConsoleAppContainer()
						self.container.execute(emu1)
						time.sleep (5)
						print "[SOFTCAM] starting cam 2 " + emu2
						self.container = eConsoleAppContainer()
						self.container.execute(emu2)
					else:
						self.container = eConsoleAppContainer()
						self.container.execute(start)
				else:
					self.session.open(MessageBox, "Prepairing " + actcam + " to start\n\n" + "Restarting Enigma2", MessageBox.TYPE_WARNING)
					TryQuitMainloop(self.session, 2)

				self["key_green"].setText(_("Restart"))
				self.ReadMenu()
		except:
			pass

	def Save_Settings(self, cam_name):
		#// Save Came Name to Settings file
		config.softcam.actCam.value = cam_name
		config.softcam.save()

	def Label_restart_Enigma2(self, index):
		#// Display warning when Enigma2 restarts with Cam
		if self.emuRgui[index] == 0:
			self["enigma2"].setText("")
		else:
			self["enigma2"].setText("Enigma2 restarts with cam")

	def read_startconfig(self, item):
		Adir = "/var/etc/autostart/start-config"
		be = []
		if os.path.exists(Adir) is True:
			f = open( Adir, "r" )
			be = f.readlines()
			f.close
			for line in be:
				if line.find(item) > -1:
					k = line.split("=")
					if k[1][:-1] == "y":
						return True
						break