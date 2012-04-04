from server.main import ReviewBotHTTPServer


def main():
    try:
        print "REVIEWBOT: Starting HTTP server."
        ReviewBotHTTPServer()
    except KeyboardInterrupt:
        print "REVIEWBOT: Shutting down."

if __name__ == "__main__":
    main()
