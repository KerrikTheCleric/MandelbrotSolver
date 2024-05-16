import socket
import sys
import numpy
import pickle

"""
 Listens on the specified port and takes requests to calculate a portion of the Mandelbrot problem.
 The result is then sent back to the client. The server continues to receive requests until it receives a termination message.
"""

# Example execution: python server.py localhost 4444

BUFFER_SIZE = 1024 

def run(conn):

	"""
	Main logic. Takes a request, checks its validity, calculates the result and sends it back to the connected client.
	Closes the connection upon error or termination message.
	"""

	request_list = receive_request(conn)
	res = check_request(request_list)
	
	if res == 0:
		print("SERVER ERROR: Illegitimate format in sent request. ", end = '', file=sys.stderr)
		print("Correct format is: GET/mandelbrot/{min_c_re}/{min_c_im}/{max_c_re}/{max_c_im}/{x}/{y}/{inf_n}/{y_min}/{y_max}", file=sys.stderr)
		conn.close()
		exit(1)
	if res == 2:
		print('Server ceasing operations')
		conn.close()
		exit(1)
		
	transform_request_list(request_list)
	result_list = mandelbrot_set(request_list[2], request_list[3], request_list[4], request_list[5], request_list[6], request_list[7], request_list[8], (request_list[9], request_list[10]))
	
	data = pickle.dumps(result_list)
	conn.send(data)
	
	print('Data transferred.')


def receive_request(conn):
	"""
	Receives a work request from the client
	:return: A list of all the request data.
	"""

	while 1:
		data = conn.recv(BUFFER_SIZE)
		if not data: break
		print ("received data:", data)
		request_list = data.decode().split("/")
		break
		
	return request_list
	
def check_request(request_list):
	"""
	Checks the request list to make sure the received data is of the correct format.
	:return: 0 if the format is incorrect, 1 if it is correct, 2 if it's a termination message.
	"""
	
	if request_list[0] == 'POST' and request_list[1] == 'quit':
		return 2
	elif request_list[0] != 'GET' or request_list[1] != 'mandelbrot':
		return 0
	elif len(request_list) != 11:
		return 0
		
	for x in range(2, 11):
		try:
			float(request_list[x])
		except ValueError:
			return 0
		
	return 1
	
def transform_request_list (request_list):
	"""
	Transforms the request list items to their proper types.
	"""

	request_list[2] = float(request_list[2])
	request_list[3] = float(request_list[3])
	request_list[4] = float(request_list[4])
	request_list[5] = float(request_list[5])
	request_list[6] = int(request_list[6])
	request_list[7] = int(request_list[7])
	request_list[8] = int(request_list[8])
	request_list[9] = int(request_list[9])
	request_list[10] = int(request_list[10])
	
	
def mandelbrot(z,maxiter):
	"""
	Iterates the mandelbrot set calculation for a single point
	:return: The required amount of iterations modulo 256, which is fit for the resulting grayscale image.
	"""
	
	c = z
	for n in range(maxiter):
		if abs(z) > 2:
			return n % 256
		z = z*z + c
	return maxiter % 256

def mandelbrot_set(xmin, ymin, xmax, ymax, width, height, maxiter, y_work_range):
	"""
	Main function for mandelbrot set calculation. Limits the calculation according to the provided work_range tuple.
	:return: A list single-Byte values that details the layout of the calculated image.
	"""
	
	r1 = numpy.linspace(ymin, ymax, height)
	r2 = numpy.linspace(xmin, xmax, width)
	i = y_work_range[0]
	results = []
	
	
	while i < y_work_range[1]:
		j = 0
		while j < width:
			results.append(mandelbrot(complex(r1[i], r2[j]), maxiter))
			j = j + 1
		i = i + 1
	
	print('Calculations complete.')
	return results
	

if __name__ == '__main__':

	if len(sys.argv) != 3:
		print ('Usage: server.py [IP Adress] [Port]')
		exit(1)

	TCP_IP = sys.argv[1]
	TCP_PORT = int(sys.argv[2])

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((TCP_IP, TCP_PORT)) 
	s.listen(1)

	conn, addr = s.accept()
	while 1:
		run(conn)
	
	
