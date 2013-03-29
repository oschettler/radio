#!/usr/bin/python

from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate

DEBUG = True

class Folder:
  pass

class App:
  ROWS = 2
  COLS = 16
  
  def __init__(self, lcd, folder):
    self.lcd = lcd
    self.folder = folder
    self.top = 0
    self.selected = 0

  
  def display(self):
    if self.top > len(self.folder.items) - self.ROWS:
      self.top = len(self.folder.items) self.ROWS
    
    if self.top < 0:
      self.top = 0
    
    str = ''
    for row in range(self.top, self.top + self.ROWS):
      if row > self.top:
        str += '\n'
      if row < len(self.folder.items):
        if row == self.selected:
          line = '-' + self.folder.items[row].text
          if len(line) < self.COLS:
            for row in range(len(line), self.COLS):
              line += ' '
          str += line
        else:
          line = ' ' + self.folder.items[row].text
          if len(line) < self.COLS:
            for row in range(len(line), self.COLS):
              cmd += ' '
          str += line

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
      if isinstance(self.folder.parent, Folder):
        # find the current in the parent
        itemno = 0
        index = 0
        for item in self.folder.parent.items:
          if self.folder == item:
            if DEBUG:
              print('foundit')
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
      elif isinstance(self.folder.items[self.selected], Widget):
        if DEBUG:
            print('eval', self.folder.items[self.selected].function)
        eval(self.folder.items[self.selected].function+'()')
      elif isinstance(self.folder.items[self.selected], CommandToRun):
        self.folder.items[self.selected].Run()


    def select(self):
      if DEBUG:
        print('check widget')
      if isinstance(self.cur.items[self.selected], Widget):
        if DEBUG:
          print('eval', self.folder.items[self.selected].function)
        eval(self.folder.items[self.selected].function+'()')


    def run(self):
      last_buttons = None

      while True:
        buttons = self.lcd.buttons()
        if last_buttons == buttons:
          continue
          
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



if __name__ == '__main__':
  lcd = Adafruit_CharLCDPlate()
  folder = Folder()
  app = App(lcd, folder)
  app.display()