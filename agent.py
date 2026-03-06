import zmq

def main():
    print("Agent is starting...")
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 5000)
    socket.setsockopt(zmq.LINGER, 0)

    try:
        socket.connect("tcp://localhost:5555")
        socket.send_string("quit")
        response = socket.recv_string()
        print(f"Received response: {response}")
    except zmq.error.Again:
        print("No response received within the timeout period.")
    finally:
        socket.close()
        context.term()



if __name__ == "__main__":
    main()