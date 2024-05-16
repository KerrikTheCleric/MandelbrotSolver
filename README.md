# Introduction
This is a Python program that calculates the Mandelbrot set using a client-server architecture and
produces a PGM image depicting the resulting fractal.

# Execution
A server is started using the following arguments:

> python server.py [IP_adress] [Port]

Where "IP_adress" is the adress the server should use and "Port" is the port it should listen on.

The client uses the following arguments:

> python client.py [min_c_re] [min_c_im] [max_c_re] [max_c_im] [max_n] [x] [y] [division] [List of servers]

All the arguments up to "max_n" are parameters for the mandelbrot calculations. "x" and "y"
compose the size of the resulting image (and thus the amount of detail), while "division" dictates
how many vertical chunks the workload should be divided into before being distributed among the
servers. As such, "y" needs to be evenly divisible by "division". "List of servers" is a list of servers
the client should connect to and send work to.

Example run of the program, where each line is run on a different terminal, either on the same
computer or on different ones:

> python server.py localhost 3333
> python server.py localhost 4444
> python client.py -1 -1.5 2 1.5 300 1000 1000 5 localhost:3333 localhost:4444

This divides the 1000*1000 pixels image into 5 vertical 200 pixel chunks that get divided among
the two servers. The servers then work through one chunk at a time (with one server getting 3
chunks while the other gets 2), sending the resulting data back to the client when ready. It is then
written to the resulting image by the client. Note that all servers must be started before the client so
that they can connect properly.

# Workings

Client

Using its input parameters, the client creates descriptions of work and then allocates it to as many
threads as there are servers. Each thread connects to its appropriate server and sends a message
containing information on a chunk of work and waits for the server to send back the resulting image
information. Said information is then put in the correct index in a list shared by all threads. This
process repeats until all the work is done, at which point the thread sends a termination message to
the server and concludes itself. Once all the threads have been joined by the master thread, the
result list is written into a PGM-file, producing an image of the fractals.

Server

A server sits and listens on its specified port until a client thread connects. Then, it will parse a
request message and either calculate the requested data or terminate, depending on the message.
Once calculations are complete, the data will be sent to the client thread and the server will wait
until the next message.
