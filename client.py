import socket
import sys
import pickle
import copy
import threading as threading

"""
 Divides the work among a set of threads that interact with one server each and send it a series of work requests.
 Once all servers are done, the resulting data is written to the resulting file.
"""

# Example execution: python client.py -1 -1.5 2 1.5 270 500 500 4 localhost:3333
# Example execution: python client.py -1 -1.5 2 1.5 270 500 500 4 localhost:3333 localhost:4444


BUFFER_SIZE = 157286400
BASE_MESSAGE = ("")

def check_arguments ():
	"""
	Checks the arguments to make sure the inputted data is of the correct format.
	:return: A list of arguments checked for errors.
	"""

	if len(sys.argv) < 10:
		print ('Usage: client.py [min_c_re] [min_c_im] [max_c_re] [max_c_im] [max_n] [x] [y] [division] [List of servers]')
		exit(1)
		
	for x in range(1, 9):
		try:
			float(sys.argv[x])
		except ValueError:
			print("CLIENT ERROR: Non-numerical argument provided where numerical argument is required.", file=sys.stderr)
			exit(1)
	
	argument_list = copy.deepcopy(sys.argv)
	transform_argument_list(argument_list)
	
	y = argument_list[7]
	d = argument_list[8]
	
	if y%d is not 0:
		print("CLIENT ERROR: Divisor does not cleanly divide image height.", file=sys.stderr)
		exit(1)
		
	return argument_list
	
	
def transform_argument_list (argument_list):
	"""
	Transforms the argument list items to their proper types.
	"""

	argument_list[1] = float(argument_list[1])
	argument_list[2] = float(argument_list[2])
	argument_list[3] = float(argument_list[3])
	argument_list[4] = float(argument_list[4])
	argument_list[5] = int(argument_list[5])
	argument_list[6] = int(argument_list[6])
	argument_list[7] = int(argument_list[7])
	argument_list[8] = int(argument_list[8])
	
def construct_base_message():
	"""
	Constructs the base message of a request using the inputted arguments.
	"""

	base_message = 'GET/mandelbrot'
	
	base_message = base_message + '/' + str(sys.argv[1])
	base_message = base_message + '/' + str(sys.argv[2])
	base_message = base_message + '/' + str(sys.argv[3])
	base_message = base_message + '/' + str(sys.argv[4])
	base_message = base_message + '/' + str(sys.argv[6])
	base_message = base_message + '/' + str(sys.argv[7])
	base_message = base_message + '/' + str(sys.argv[5])
	
	return base_message
	
def finalize_message(y_work_range):
	"""
	Finalizes the request message using the apropriate work range.
	"""

	finalized_message = copy.deepcopy(BASE_MESSAGE)
	
	finalized_message = finalized_message + '/' + str(y_work_range[0])
	finalized_message = finalized_message + '/' + str(y_work_range[1])
	
	return finalized_message
	
def calculate_y_work_ranges(height, divisor):
	"""
	Calculates the work ranges for each request.
	:return: A list of work ranges.
	"""

	work_ranges = []
	interval = height / divisor
	
	for i in range(0, divisor):
		work_ranges.append((int(i * interval), int((i+1) * interval)))

	interval = height / divisor
	
	return work_ranges
	
def divide_work(work_ranges, argument_list, server_count):
	"""
	Divides the work among the threads.
	:return: A list containing information on which server a thread should communicate with,
	what work requests they should make and at what indices the resulting data should be stored in within the result list.
	"""
	
	work_list = [[], [], []]
	
	for i in range(0, server_count):
		work_list[0].append(argument_list[i + 9])
		work_list[1].append([])
		work_list[2].append([])
		
	j = 0
	for i in range(0, len(work_ranges)):
		work_list[1][j].append(work_ranges[i])
		work_list[2][j].append(i)
		if j == (server_count-1):
			j = 0
		else:
			j = j + 1
		
	return work_list
	
class ServerCommunicatorThread(threading.Thread):
	"""
	Thread class that handles communication with a server, collects the resulting
	image data and stores it in the thread's shared result list.
	"""

	def __init__(self, result_list, server, work_ranges, indices_list):
		threading.Thread.__init__(self)
		self.result_list = result_list
		self.server = server
		self.work_ranges = work_ranges
		self.indices_list = indices_list
		

	def run(self):
		"""
		Main function. Loops through the available work and then sends a 
		termination message to the connected server.
		"""
		
		self.server = self.server.split(':')
		termination_message = 'POST/quit'
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((self.server[0], int(self.server[1])))
		
		loops = len(self.work_ranges)

		for i in range(0, loops):
			finalized_message = finalize_message(self.work_ranges[i])
			j = self.indices_list[i]
			s.send(finalized_message.encode('UTF-8'))
			self.result_list[j] = pickle.loads(s.recv(BUFFER_SIZE))
			
		s.send(termination_message.encode('UTF-8'))
		s.close()
	
def create_image(width, height, data, rows):
	"""
	Creates a PGM-image showing the result of the mandelbrot set calculation in grayscale.
	"""

	filename = 'result.pgm'
	try:
		file=open(filename, 'wb')
	except IOError:
		print("CLIENT ERROR: Cannot open file: result.pgm", file=sys.stderr)
		exit(1)
		
	pgmHeader = 'P5' + '\n' + str(width) + '  ' + str(height) + '  ' + str(255) + '\n'
	file.write(pgmHeader.encode())
	
	for i in range(0, rows):
		binary_format = bytearray(data[i])
		file.write(binary_format)
	
	file.close()

if __name__ == '__main__':
	
	argument_list = check_arguments()
	BASE_MESSAGE = construct_base_message()
	server_count = (len(sys.argv) - 9)
	
	work_ranges = calculate_y_work_ranges(argument_list[7],  argument_list[8])
	work_list = divide_work(work_ranges, argument_list, server_count)
	result_list = [None] * len(work_ranges)
	
	threads = []
	for i in range(0, server_count):
		thread = ServerCommunicatorThread(result_list, work_list[0][i], work_list[1][i], work_list[2][i])
		threads.append(thread)
		thread.start()
		
	for thread in threads:
		thread.join()
	
	create_image(argument_list[6], argument_list[7], result_list, len(work_ranges))
	print('Result image created.')