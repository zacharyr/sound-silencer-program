#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author: Zach Rohde (zach@zachrohde.com)

For more information go to: http://zachrohde.com
"""

import ConfigParser
import os
import subprocess
import time
import win32api, win32con
import wx

from threading import *

# Button definition to stop threads.
ID_STOP = wx.NewId()

# Define notification events for thread completion.
SELECT_EVT_RESULT_ID = wx.NewId()
LAUNCH_EVT_RESULT_ID = wx.NewId()

# Define result event for Key Selection thread.
def SELECT_EVT_RESULT(win, func):
    win.Connect(-1, -1, SELECT_EVT_RESULT_ID, func)

# Define result event for Program Launch thread.
def LAUNCH_EVT_RESULT(win, func):
    win.Connect(-1, -1, LAUNCH_EVT_RESULT_ID, func)

class SelectResultEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(SELECT_EVT_RESULT_ID)
        self.data = data

class LaunchResultEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(LAUNCH_EVT_RESULT_ID)
        self.data = data

# Thread class for Key Selection process.
class KeySelectThread(Thread):
    def __init__(self, notify_window):
        Thread.__init__(self)
        self._notify_window = notify_window
        self._want_abort = 0
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()
    
    def run(self):
        config = ConfigParser.RawConfigParser()
        config.add_section('MainConfiguration')
        
        while(True):
            time.sleep(1)
            # Each second, scan each of the keyboards keys to detect a keystroke.
            for x in range(256):
                input = win32api.GetAsyncKeyState(x)
                # To remove false-positives, user must double hit the key to register the last used key or first hit, 
                # as the designated key.
                if input is 1:
                    # Ignore the left mouse click or x = 1.
                    if x is not 1:
                        key = str(hex(x)) # Value is integer, convert to hex, then string for parcing.
                        
                        config.set('MainConfiguration', 'keyboard_key', key)
                        
                        with open('config.cfg', 'wb') as configfile:
                            config.write(configfile)
                        
                        wx.PostEvent(self._notify_window, SelectResultEvent(key))
                        return
            
            # Use a result of None to acknowledge the abort (of
            # course you can use whatever you'd like or even
            # a separate event type).
            if self._want_abort:
                wx.PostEvent(self._notify_window, SelectResultEvent(None))
                return
    
    # Method for use by main thread to signal an abort.
    def abort(self):
        self._want_abort = 1
        
# Thread class for Program Launch process.
class SoundSilencerThread(Thread):
    def __init__(self, notify_window):
        Thread.__init__(self)
        self._notify_window = notify_window
        self._want_abort = 0
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()
    
    def run(self):
        key = win32con.VK_CONTROL # Left control.
        key_pressed = False # Determine whether key has been pressed.
        number_of_mutes = 0 # We only want to mute one time per key hit (the while(True) loop would just keep muting/unmuting)).
        
        # Parse config.cfg for settings.
        config = ConfigParser.ConfigParser()
        config.read('config.cfg')
        key = config.get('MainConfiguration', 'keyboard_key', 0)
        
        while(True):
            # Sleep while loop to reduce input buffer issues.
            time.sleep(0.01)
            
            # Determines whether a key is up or down at the time the function is called,
            # and whether the key was pressed after a previous call to GetAsyncKeyState.
            state = win32api.GetAsyncKeyState(int(key,0))
            
            # When state is not 0, key is being pressed.
            if state is not 0:
                # Keep number of mutes to 0 in order to mute the sound just once (calling VK_VOLUME_MUTE again unmutes!).
                if number_of_mutes == 0:
                    lower_volume = win32api.keybd_event(win32con.VK_VOLUME_MUTE, 0, 0, 0)
                    key_pressed = True
                    number_of_mutes = number_of_mutes + 1
                    
                    wx.PostEvent(self._notify_window, LaunchResultEvent(str(key_pressed)))
            
            # Check to see if key has been pressed and whether the state is 0 (to keep the volume down when holding key).
            if key_pressed is True and state is 0:
                raise_volume = win32api.keybd_event(win32con.VK_VOLUME_MUTE, 0, 0, 0)
                key_pressed = False
                number_of_mutes = 0
            
            # Use a result of None to acknowledge the abort (of
            # course you can use whatever you'd like or even
            # a separate event type).
            if self._want_abort:
                wx.PostEvent(self._notify_window, LaunchResultEvent(None))
                return
    
    # Method for use by main thread to signal an abort.
    def abort(self):
        self._want_abort = 1

class Interface(wx.Frame):
    def __init__(self, parent, config, *args, **kwargs):
        super(Interface, self).__init__(parent, style = wx.MINIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION, *args, **kwargs)
        
        # Set up event handlers for any worker thread results.
        SELECT_EVT_RESULT(self, self.OnSelectResult)
        LAUNCH_EVT_RESULT(self, self.OnLaunchResult)
        self.worker = None # And indicate we don't have a worker threads yet.
        
        self._config = config
        self.InitUI()
    
    def InitUI(self):
        global launch_btn
        
        # Menu Bar Items
        menubar = wx.MenuBar()
        
        fileMenu = wx.Menu()
        
        helpMenu = wx.Menu()
        
        hm_about = wx.MenuItem(fileMenu, wx.ID_ABOUT, '&About')
        helpMenu.AppendItem(hm_about)
        self.Bind(wx.EVT_MENU, self.OnAbout, hm_about)
        menubar.Append(helpMenu, '&Help')
        
        self.SetMenuBar(menubar)
        
        # Buttons
        pnl = wx.Panel(self)
        
        launch_btn = wx.Button(pnl, label='Launch Sound Silencer', pos=(96, 70))
        launch_btn.Bind(wx.EVT_BUTTON, self.OnLaunchStart)
        
        select_key_btn = wx.Button(pnl, label='Select Silencing Keyboard Key', pos=(78, 100))
        select_key_btn.Bind(wx.EVT_BUTTON, self.OnSelectStart)
        
        close_btn = wx.Button(pnl, ID_STOP, label='Close', pos=(121, 130))
        close_btn.Bind(wx.EVT_BUTTON, self.OnStop, id=ID_STOP)
        
        # Labels
        self.status_label = wx.StaticText(pnl, label='Program Status: ', pos=(10, 5))
        self.status = wx.StaticText(pnl, label='No actions currently being performed.', pos=(95, 5))
        
        self.key_label = wx.StaticText(pnl, label='Current Key Set: ', pos=(10, 25))
        try:
            key = self._config.get('MainConfiguration', 'keyboard_key', 0)
            self.key = wx.StaticText(pnl, label='%s' % key, pos=(97.5, 25))
        except ConfigParser.NoSectionError:
            self.key = wx.StaticText(pnl, label='No key currently set.', pos=(97.5, 25))
            launch_btn.Disable()
        
        # General program options.
        self.SetSize((325, 210)) #300
        self.SetTitle('Sound Silencer Program')
        self.Centre()
        self.Show(True)
    
    # Trigger the KeySelect worker thread unless it's already busy.
    def OnSelectStart(self, event):
        if not self.worker:
            self.worker = KeySelectThread(self)
            self.status.SetLabel('Selecting default key...')
    
    # Trigger the SoundSilencer worker thread unless it's already busy.
    def OnLaunchStart(self, event):
        if not self.worker:
            self.worker = SoundSilencerThread(self)
            self.status.SetLabel('Launching Sound Silencer... press set key...')
    
    # Flag the worker thread to stop if running.
    def OnStop(self, event):
        if self.worker:
            self.worker.abort()
            time.sleep(0.01)
            self.OnQuit(event)
        else:
            self.OnQuit(event)
    
    def OnSelectResult(self, event):
        if event.data is None:
            # Thread aborted (using our convention of None return).
            self.status.SetLabel('Error: Process aborted!')
        else:
            # Process results.
            self.status.SetLabel('Key set successfully!')
            launch_btn.Enable()
            self.key.SetLabel('%s' % event.data)
        # In either event, the worker is done.
        self.worker = None
    
    def OnLaunchResult(self, event):
        if event.data is None:
            # Thread aborted (using our convention of None return).
            self.status.SetLabel('Error: Process aborted!')
        else:
            # Process results.
            self.status.SetLabel('Sound Silencer is now running.')
    
    def OnAbout(self, event):
        # About dialog information.
        description = """Sound Silencer is a simple python program designed to silence all background noises on keystroke, so that you can peacefully talk on your microphone."""
        info = wx.AboutDialogInfo()
        info.SetName('Sound Silencer')
        info.SetVersion('v1.0')
        info.SetDescription(description)
        info.SetCopyright('Author: Zach Rohde')
        info.SetWebSite('http://zachrohde.com')
        
        wx.AboutBox(info)
    
    def OnQuit(self, event):
        self.Close(True)

def main():
    # Parse config.cfg for settings.
    config = ConfigParser.ConfigParser()
    config.read('config.cfg')
    
    app = wx.App(0)
    gui = Interface(None, config)
    app.MainLoop()

if __name__ == '__main__':
    main()