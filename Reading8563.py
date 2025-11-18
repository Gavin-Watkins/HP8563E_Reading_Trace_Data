#Program to read the trace data from a HP 8563E spectrum analyser
#This should work with most 85 series spectrum analysers, but the SCPI commands maybe different, check in manual
#Result plotted on the screen at the moment, but I'll modify this to write to file, copy to clipboard or process further
#For use with a Prologix serial to USB adapter, note that this emulates an RS232 serial port

import pyvisa
import struct
import matplotlib.pyplot as plt
import numpy as np
processed_data = []
i = 0
freq_left = 2400 #set the lower frequency range
freq_right = 2500 #set the upper frequency range

resource_name = 'ASRL3::INSTR' #ASRL3 is the serial port that my Prologix adapter appears on, but maybe different for other people

# The GPIB address of your spectrum analyzer which can be set on the analyser
gpib_address = 18

try:
    # Initialize the resource manager
    rm = pyvisa.ResourceManager()
    print(rm.list_resources())
    # Open the connection to the Prologix adapter
    prologix = rm.open_resource(resource_name)

    # === Configure the Prologix adapter (Optional but recommended) ===
    # For a USB adapter, configure the Prologix to automatically address
    # the device before each command.
    # Note: These are adapter-specific commands, not SCPI.
    prologix.write("++mode 1") # Use controller mode
    prologix.write("++auto 1") # Enable read-after-write
    prologix.write(f"++addr {gpib_address}") # Set the device address

    # === Communicate with the spectrum analyzer ===
    print('pink') #this is just a flag I moved around in the code to help me debug when it hung
    # Query the instrument's identification
    idn = prologix.query("ID?")

    print(f"Connected to: {idn}") #should return something like "HP8563E,026,UK6"

    #Set the spec anz lower frequency (FA) and upper frequency (FB) if needed
    prologix.write(f"FA {freq_left} MHZ")
    prologix.write(f"FB {freq_right} MHZ")

    # Read the trace data
    trace_data_raw = prologix.query("TRA?")# for HP8563E TRA is hte command for the trace data, but this maybe different for other analysers

    actual_data_points = int((len(trace_data_raw))/7) #Data is sent back as ascii characters, something like "-", "7", "3", ".", "0", "0", ",". Seven characters per value
    print(f"Read {actual_data_points} actual data points.") #typically the HP8563E takes 601 points, so sends 4207 ascii characters
    print("Trace data (first 20 points):", trace_data_raw[4200:]) #Just a quick check
    #Need to put in a loop here to go through trace_data_raw to rearrange it into the integers
    for i in range(actual_data_points):
        truevalue=10*int(trace_data_raw[1+(7*i)])+int(trace_data_raw[2+(7*i)])+0.1*int(trace_data_raw[4+(7*i)])+0.01*int(trace_data_raw[5+(7*i)])
        if (trace_data_raw[7*i]) == '-':
            truevalue = truevalue * -1
        processed_data.append(truevalue)

    # Plot a quick graph with Matplotlib
    x_axis = np.linspace(freq_left, freq_right, actual_data_points)
    plt.plot(x_axis,processed_data)
    plt.show()

except pyvisa.errors.VisaIOError as e:
    print(f"An error occurred: {e}")
except struct.error as e:
    print(f"Binary data unpacking error: {e}. Check data format and endianness.")

prologix.close() #Probably a good idea to close them
rm.close() #I did sometimes find things would hang and resetting my USB hub helped a lot