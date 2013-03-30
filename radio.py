#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# A simple internet radio for RaspberryPI
# Based on mpd/mpc and the Character LCD Plate by Adafruit
#
# The basic navigation code is based on lcdmenu.py by Alan Aufderheide
#
# Copyright (c) 2013 Olav Schettler
# Open source. MIT license
#

from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
import re
import shlex, subprocess
from time import strftime, sleep
from unidecode import unidecode

DEBUG = False

def fixed_length(str, length):
  'Truncate and pad str to length'
  return ('{:<%d}' % length).format(str[:length])


class Node:
  '''
  Base class for nodes in a hierarchical navigation tree
  '''
  def __init__(self, text):
    self.mark = '-'
    self.parent = None
    self.text = text
  
  def into(self):
    pass
  
  def __repr__(self):
    return 'node:' + self.text


class Timer(Node):
  def __init__(self):
    self.mark = '-'
    self.parent = None
  
  def gettext(self):
    print "TT"
    return strftime('%H:%M:%S %d.%m')

  text = property(gettext)
  

class Folder(Node):
  def __init__(self, text, items=[]):
    Node.__init__(self, text)
    self.mark = '>'
    self.setItems(items)
  
  def setItems(self, items):
    self.items = items
    for item in self.items:
      item.parent = self


class Playlists(Folder):
  def __init__(self, radio):
    Folder.__init__(self, 'Playlists')
    self.radio = radio

  def into(self):
    print "into", repr(self)
    self.setItems([
      Playlist(playlist, self.radio) for playlist in self.radio.command('mpc lsplaylists')
    ])


class FinishException(Exception):
  pass


class App:
  '''
  Base class of applications and applets
  '''
  ROWS = 2
  COLS = 16
  
  def __init__(self, lcd, folder):
    self.lcd = lcd
    self.folder = folder
    self.top = 0
    self.selected = 0

  
  def display(self):
    if self.top > len(self.folder.items) - self.ROWS:
      self.top = len(self.folder.items) - self.ROWS
    
    if self.top < 0:
      self.top = 0
    
    if DEBUG:
      print '------------------'
    
    str = ''
    for row in range(self.top, self.top + self.ROWS):
      if row > self.top:
        str += '\n'
      if row < len(self.folder.items):
        if row == self.selected:
          line = self.folder.items[row].mark
        else:
          line = ' '
        
        line = fixed_length(line + self.folder.items[row].text, self.COLS)
        str += line

        if DEBUG:
          print('|' + line + '|')

    if DEBUG:
      print '------------------'

    self.lcd.home()
    self.lcd.message(str)


  def up(self):
    if self.selected == 0:
      return
    elif self.selected > self.top:
      self.selected -= 1
    else:
      self.top -= 1
      self.selected -= 1


  def down(self):
    if self.selected + 1 == len(self.folder.items):
      return
    elif self.selected < self.top + self.ROWS - 1:
      self.selected += 1
    else:
      self.top += 1
      self.selected += 1


  def left(self):
    if not isinstance(self.folder.parent, Folder):
      return 
    
    # find the current in the parent
    itemno = 0
    index = 0
    for item in self.folder.parent.items:
      if self.folder == item:
        if DEBUG:
          print 'foundit:', item
        index = itemno
      else:
          itemno += 1
    if index < len(self.folder.parent.items):
      self.folder = self.folder.parent
      self.top = index
      self.selected = index
    else:
      self.folder = self.folder.parent
      self.top = 0
      self.selected = 0


  def right(self):
    if isinstance(self.folder.items[self.selected], Folder):
      self.folder = self.folder.items[self.selected]
      self.top = 0
      self.selected = 0
      self.folder.into()
    elif isinstance(self.folder.items[self.selected], Applet):
      self.folder.items[self.selected].run()


  def select(self):
    if isinstance(self.folder.items[self.selected], Applet):
      self.folder.items[self.selected].run()


  def command(self, cmd):
    print shlex.split(cmd)
    result = subprocess.check_output(
      shlex.split(cmd), stderr=subprocess.STDOUT
    )
    result = result.rstrip().split('\n')
    print cmd, '-->', result
    return result


  def tick(self):
    '''
    In case variable information is displayed, refresh every second
    '''
    if self.ticks % 10 == 0:
      self.display()


  def run(self):
    '''
    Basic event loop of the application
    '''
    self.ticks = 0
    self.display()
    
    last_buttons = None

    while True:
      self.tick()
      self.ticks += 1
      sleep(0.1)

      buttons = self.lcd.buttons()
      if last_buttons == buttons:
        continue
      last_buttons = buttons
      
      try:
        if (self.lcd.buttonPressed(self.lcd.LEFT)):
          self.left()
          self.display()

        if (self.lcd.buttonPressed(self.lcd.UP)):
          self.up()
          self.display()

        if (self.lcd.buttonPressed(self.lcd.DOWN)):
          self.down()
          self.display()

        if (self.lcd.buttonPressed(self.lcd.RIGHT)):
          self.right()
          self.display()

        if (self.lcd.buttonPressed(self.lcd.SELECT)):
          self.select()
          self.display()
      
      except FinishException:
        return
      

class Radio(App):
  '''
  The application.
  '''
  def __init__(self):
    self.command('mpc stop')

    App.__init__(self,
      Adafruit_CharLCDPlate(), 
      Folder('Pauls iRadio', (
        Playlists(self),
        Folder('Settings', (
          Node(self.command('hostname -I')[0]), 
          Timer(), 
        )),
      ))
    )


class Applet(App):
  def __init__(self, text, app):
    self.mark = '*'
    self.parent = None
    self.text = text
    self.app = app
    self.lcd = app.lcd

  def command(self, cmd):
    return self.app.command(cmd)

  def left(self):
    return

  def right(self):
    return

  def up(self):
    return

  def down(self):
    return

  def select(self):
    return


class Playlist(Applet):
  volumes = (0, 60, 70, 80, 85, 90, 95, 100)
  
  def display(self):
    self.lines = (
      unidecode(self.command('mpc -f %name% current')[0].split(',', 1)[0]),
      unidecode(self.command('mpc -f %title% current')[0]),
    )
    
    self.volume = int(re.search(r'\d+', 
      self.command('mpc volume')[0]
    ).group())
    
    self.dir = 'L'
    self.shift = 0


  def tick(self):
    if self.ticks % 5 != 0:
      return
      
    if self.lines[0] == '':
      self.command('mpc volume 70')
      self.display()
      return

    str = ''
    str += fixed_length(self.lines[0], self.COLS)
    str += '\n' + fixed_length(self.lines[1][self.shift:], self.COLS)
    if DEBUG:
      print '------------------'
      for line in str.split('\n'):
        print '|' + line + '|'
      print '------------------'
    
    self.lcd.home()
    self.lcd.message(str)
    
    if self.dir == 'L':
      if self.shift + self.COLS < len(self.lines[1]):
        self.shift += 1
      else:
        self.dir = 'R'
    else:
      if self.shift > 0:
        self.shift -= 1
      else:
        self.display()


  def run(self):
    self.command('mpc clear')
    self.command('mpc load ' + self.text)
    self.command('mpc play')

    Applet.run(self)

  def left(self):
    'Return from applet'
    raise FinishException
  
  def up(self):
    try:
      pos = self.volumes.index(self.volume)
    except:
      pos = 0

    if pos < len(self.volumes):
      self.command('mpc volume %d' % self.volumes[pos + 1]) 

  def down(self):
    try:
      pos = self.volumes.index(self.volume)
    except:
      pos = 0

    if pos > 0:
      self.command('mpc volume %d' % self.volumes[pos - 1]) 


if __name__ == '__main__':
  Radio().run()