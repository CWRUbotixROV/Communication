from tkinter import * #imports everything from the tkinter library
import time
import random
from ssh import SSH
from marker_dropper import MarkerDropper
from functools import partial

class SettableText(Text):
    """Extends the tkinter Text object to allow the text to be changed."""

    def set_text(self, newtext):
        """Set the text in the text object to the new text.

        :param str newtext: the text to set the Text object to hold

        """
        # remove all the old text
        self.delete(1.0, END)

        # add the new text
        self.insert(END, newtext)


class ThrusterControl():
    """Class to represent and configure a thruster on the BabyROV."""

    def __init__(self, ssh, text_output):
        """Create a new ThrusterControl object

        :param string name:     an arbitrary name for the thruster
        :param obj ssh:         an SSH object to send commands to the Pi over
        :param obj text_output: a SettableText object that output is printed to

        """
        self.forward = False
        self.backward = False

        self.text_output = text_output
        self.thruster_forward_off()
        self.thruster_backward_off()

        self.ssh = ssh

    def thruster_forward(self, event=None):
        """Sends the command to turn on the thruster and updates the GUI.

        Note that the thruster on command is only sent if the thruster is not already on.

        :param obj event: obj with the event information that called this function

        """
        if not self.forward and not self.backward:
            self.text_output.set_text('Thruster Forward')
            self.forward = True

    def thruster_backward(self, event=None):
        if not self.forward and not self.backward:
            self.text_output.set_text('Thruster Backward')
            self.backward = True

    def thruster_forward_off(self, event=None):
        """Sends the command to turn off the thruster and updates the GUI.

        :param obj event: obj with the event information that called this function

        """

        #self.ssh.exec_command('gpio write 4 0')
        self.forward = False

        if not self.backward:
            self.text_output.set_text('Thruster Off')
        else:
            self.thruster_backward()


    def thruster_backward_off(self, event=None):
        self.backward = False

        if not self.forward:
            self.text_output.set_text('Thruster Off')
        else:
            self.thruster_forward()

class ControlWindow():
    """Class to represent store all info for the GUI used to control the robot."""
    THRUSTER_BACKWARD_KEY = 's'
    THRUSTER_FORWARD_KEY = 'w'
    TEMP_SENSOR_KEY = 't'
    PH_SENSOR_KEY = 'p'
    DROP_RED_KEY = 'r'
    DROP_BLACK_KEY = 'b'

    TEMP_TEXT = "Last Temperature\nReading: {READING}"
    PH_TEXT = "Last pH Reading: \n{READING}"

    def __init__(self, use_zero=False, red=[1, 2, 3], black=[5, 6, 7]):
        self.ssh = SSH(SSH.COMPANION)

        transport = self.ssh.get_transport()
        companion_addr = (SSH.COMPANION, 22)      # the address and port of the Pi 3, as seen by the surface computer
        if use_zero:
            zero_addr = (SSH.ZERO.ip, 22)         # the address and port of the Pi Zero, as seen by the Pi 3
            channel = transport.open_channel('direct-tcpip', zero_addr, companion_addr)
            self.zero_ssh = SSH(SSH.ZERO, sock=channel)

        self.ssh.exec_and_print('sudo pigpiod')  # pigpio daemon needs to be started manually for now

        self.master = Tk()
        
        self.markerdropper = MarkerDropper(270, 40, red_markers=red, black_markers=black, pin=20)

        self._add_instructions()
        self._setup_thrusters()
        self._setup_sensors()

        self._bind_keys()

        self.master.mainloop()

    def _add_instructions(self):
        """Adds the instruction text box to the GUI."""
        instructions = Text(self.master, height=14, width=40)

        instructions.insert(END, 'Baby ROV Control:\n'
                                 'Press <{}> to move forward\n'
                                 'Press <{}> to move backward\n'
                                 '\nSensor Readings\n'
                                 'Press <{}> to get a temperature reading\n'
                                 'Press <{}> to get a pH reading.\n'
                                 'Press <{}> to drop a red marker.\n'
                                 'Press <{}> to drop a black marker.\n'
                                 ''.format(self.THRUSTER_FORWARD_KEY,
                                           self.THRUSTER_BACKWARD_KEY,
                                           self.TEMP_SENSOR_KEY,
                                           self.PH_SENSOR_KEY,
                                           self.DROP_RED_KEY,
                                           self.DROP_BLACK_KEY))

        # place the instruction at the top of the GUI window
        instructions.grid(row=0, column=0, columnspan=2)
        instructions.grid()

    def _setup_thrusters(self):
        """Adds the thruster info boxes to the GUI."""
        # create text box for left thruster on left under the instructions
        self.thruster_state = SettableText(self.master, height=1, width=40)
        self.thruster_state.grid(row=1, column=0,  columnspan=2)

        # create control object for left thruster
        self.thruster = ThrusterControl(None, self.thruster_state)

    def _setup_sensors(self):
        """Adds the pH and temperature info boxes to the GUI."""
        # create the text box for pH reading under the left thruster
        self.ph_reading = SettableText(self.master, height=2, width=20)
        self.ph_reading.grid(row=2, column=0)
        self.ph_reading.set_text(self.PH_TEXT.format(READING='N/A'))

        # create the text box for temperature reading under the right thruster
        self.temp_reading = SettableText(self.master, height=2, width=20)
        self.temp_reading.grid(row=2, column=1)
        self.temp_reading.set_text(self.TEMP_TEXT.format(READING='N/A'))

    def _bind_keys(self):
        """Bind the keys for the peripherals (ie thrusters, sensors, etc)."""
        # bind the right thruster key to turn it on and off
        self.master.bind('<KeyPress-{}>'.format(self.THRUSTER_FORWARD_KEY),
                         self.thruster.thruster_forward)
        self.master.bind('<KeyRelease-{}>'.format(self.THRUSTER_FORWARD_KEY),
                         self.thruster.thruster_forward_off)

        # bind the left thruster key to turn it on and off
        self.master.bind('<KeyPress-{}>'.format(self.THRUSTER_BACKWARD_KEY),
                         self.thruster.thruster_backward)
        self.master.bind('<KeyRelease-{}>'.format(self.THRUSTER_BACKWARD_KEY),
                         self.thruster.thruster_backward_off)

        # bind the temperature sensor key
        self.master.bind('<KeyPress-{}>'.format(self.TEMP_SENSOR_KEY),
                         self.read_temp_sensor)

        # bind the pH sensor key
        self.master.bind('<KeyPress-{}>'.format(self.PH_SENSOR_KEY),
                         self.read_ph_sensor)
        
        # bind the keys to drop red and black markers, using a partial function to repeat less code
        self.master.bind(f'<KeyPress-{self.DROP_RED_KEY}>', partial(self.drop_marker, red=True))
        self.master.bind(f'<KeyPress-{self.DROP_BLACK_KEY}>', partial(self.drop_marker, red=False))

    def read_temp_sensor(self, event=None):
        """Sends the SSH command to read the temperature sensor and updates its info box.

        :param obj event: obj with the event information that called this function

        """
        # send the read command
        reading = self.ssh.exec_and_print('python ~/temp_reading.py')
        #reading = random.randint(1, 14)

        # update the GUI text box
        self.temp_reading.set_text(self.TEMP_TEXT.format(READING=reading))

    def read_ph_sensor(self, event=None):
        """Sends the SSH command to read the pH sensor and updates its info box.

        :param obj event: obj with the event information that called this function

        """
        # send the read command
        reading = self.ssh.exec_and_print('python ph_reading.py')
        #reading = random.randint(0, 100)

        # update the GUI text box
        self.ph_reading.set_text(self.PH_TEXT.format(READING=reading))
    
    def drop_marker(self, event=None, red=True):
        """
        Drops a marker.

        Arguments:
            red (bool): True if a red marker should be dropped, False if a black one should be dropped
        """
        if red:
            cmd, has_markers = self.markerdropper.drop_red_marker()
        else:
            cmd, has_markers = self.markerdropper.drop_black_marker()
        print(cmd)
        if has_markers:
            self.ssh.exec_and_print(cmd)
            self.markerdropper.success()
    
if __name__ == "__main__":
    x = ControlWindow()
