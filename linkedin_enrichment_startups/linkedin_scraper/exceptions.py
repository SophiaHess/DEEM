class InvalidFounderURLException(Exception):
    def __init__(self):
        Exception.__init__(self, 'Founder URL redirected to Error 404 on Linkedin')
