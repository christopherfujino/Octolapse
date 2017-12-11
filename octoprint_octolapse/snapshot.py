# coding=utf-8
import os
import sys
import time
import utility
import requests
import threading
from requests.auth import HTTPBasicAuth
from io import open as iopen
from urlparse import urlsplit
from math import trunc
from .settings import *
import traceback
import shutil
import camera
import uuid


	
class CaptureSnapshot(object):

	def __init__(self, settings,dataDirectory, printStartTime, printEndTime=None):
		self.Settings = settings
		self.Printer = self.Settings.CurrentPrinter()
		self.Snapshot = self.Settings.CurrentSnapshot()
		self.Camera = self.Settings.CurrentCamera()
		self.PrintStartTime = printStartTime
		self.PrintEndTime = printEndTime
		self.DataDirectory = dataDirectory
			
	def Snap(self,printerFileName,snapshotNumber,onComplete=None,onSuccess=None, onFail=None):
		
		
		info = SnapshotInfo(self.Snapshot.output_filename, printerFileName, self.PrintStartTime,  self.Snapshot.output_format)
		# set the file name.  It will be a guid + the file extension

		snapshotGuid = str(uuid.uuid4())
		info.FileName = "{0}.{1}".format(snapshotGuid, self.Snapshot.output_format)
		info.DirectoryName = utility.GetDirectoryFromTemplate(self.Snapshot.output_directory,self.DataDirectory, printerFileName, self.PrintStartTime, self.Snapshot.output_format)
		url = camera.FormatRequestTemplate(self.Camera.address, self.Camera.snapshot_request_template,"")
		
		SnapshotJob(self.Settings, info, url, snapshotGuid, timeoutSeconds = self.Snapshot.delay/1000.0*2, onComplete = onComplete, onSuccess=onSuccess, onFail = onFail).Process()

	
def requests_image(file_url,path):
    suffix_list = ['jpg', 'gif', 'png', 'tif', 'svg',]
    file_name =  urlsplit(file_url)[2].split('/')[-1]
    file_suffix = file_name.split('.')[1]
    i = requests.get(file_url)
    if file_suffix in suffix_list and i.status_code == requests.codes.ok:
        with iopen(file_name, 'wb') as file:
            file.write(i.content)
    else:
        return False
class SnapshotJob(object):
	snapshot_job_lock = threading.RLock()
	
	def __init__(self,settings, snapshotInfo, url,  snapshotGuid, timeoutSeconds=5, onComplete = None, onSuccess = None, onFail = None):
		camera = settings.CurrentCamera()
		self.Address = camera.address
		self.Username = camera.username
		self.Password = camera.password
		self.IgnoreSslError = camera.ignore_ssl_error
		self.Settings = settings;
		self.SnapshotInfo = snapshotInfo;
		self.Url = url
		self.TimeoutSeconds = timeoutSeconds
		self.SnapshotGuid = snapshotGuid
		self._on_complete = onComplete
		self._on_success = onSuccess
		self._on_fail = onFail
	def Process(self):
		#TODO:  REPLACE THE SNAPSHOT NUMBER WITH A GUID HERE
		self._thread = threading.Thread(target=self._process, name="SnapshotDownloadJob_{name}".format(name = self.SnapshotGuid))
		self._thread.daemon = True
		self._thread.start()
	def _process(self):
		with self.snapshot_job_lock:
			success = False
			dir = "{0:s}{1:s}".format(self.SnapshotInfo.DirectoryName, self.SnapshotInfo.FileName)
			r=None
			try:
				if(len(self.Username)>0):
					self.Settings.CurrentDebugProfile().LogSnapshotDownload("Snapshot Download - Authenticating and downloading from {0:s} to {1:s}.".format(self.Url,dir))
					r=requests.get(self.Url, auth=HTTPBasicAuth(self.Username, self.Password),verify = not self.IgnoreSslError,timeout=float(self.TimeoutSeconds))
				else:
					self.Settings.CurrentDebugProfile().LogSnapshotDownload("Snapshot - downloading from {0:s} to {1:s}.".format(self.Url,dir))
					r=requests.get(self.Url,verify = not self.IgnoreSslError,timeout=float(self.TimeoutSeconds))

				if r.status_code == requests.codes.ok:
					try:
						path = os.path.dirname(dir)
						if not os.path.exists(path):
							os.makedirs(path)
					except:
						type = sys.exc_info()[0]
						value = sys.exc_info()[1]
						self.Settings.CurrentDebugProfile().LogWarning("Download - An exception was thrown when trying to save a snapshot to: {0} , ExceptionType:{1}, Exception Value:{2}".format(os.path.dirname(dir),type,value))
						return
					try:
						with iopen(dir, 'wb') as file:
							for chunk in r.iter_content(1024):
								if chunk:
									file.write(chunk)
							self.Settings.CurrentDebugProfile().LogSnapshotSave("Snapshot - Snapshot saved to disk at {0}".format(dir))
							success = True
					except:
						type = sys.exc_info()[0]
						value = sys.exc_info()[1]
						self.Settings.CurrentDebugProfile().LogError("Snapshot - An exception of type:{0} was raised while saving the retrieved shapshot to disk: Error:{1} Traceback:{2}".format(type, value, traceback.format_exc()))
				else:
					self.Settings.CurrentDebugProfile().LogWarning("Snapshot - failed with status code:{0}".format(r.status_code))
			except:
				type = sys.exc_info()[0]
				value = sys.exc_info()[1]
				self.Settings.CurrentDebugProfile().LogError("Download - An exception of type:{0} was raised during snapshot download:Error:{1}".format(type, value))

			if(success):
				self._notify_callback("success", self.SnapshotInfo)
			else:
				self._notify_callback("fail")

			self._notify_callback("complete")
				
	def _notify_callback(self, callback, *args, **kwargs):
		"""Notifies registered callbacks of type `callback`."""
		name = "_on_{}".format(callback)
		method = getattr(self, name, None)
		if method is not None and callable(method):
			method(*args, **kwargs)
class SnapshotInfo(object):
	def __init__(self, outputFileName, printerFileName, printStartTime, outputExtension):
		self._outputFileName = outputFileName
		self._printerFileName = printerFileName
		self._printStartTime = printStartTime
		self._outputExtension = outputExtension
		self.FileName = ""
		self.DirectoryName = ""
	def GetTempFullPath(self):
		return "{0}{1}{2}".format(self.DirectoryName, os.sep, self.FileName)
	def GetFullPath(self, snapshotNumber):
		return  "{0}{1}".format(self.DirectoryName, utility.GetSnapshotFilenameFromTemplate(self._outputFileName, self._printerFileName, self._printStartTime, self._outputExtension,snapshotNumber))
						  
