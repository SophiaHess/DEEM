class NoDegreeException(Exception):
    def __init__(self):
        Exception.__init__(self, 'Degree not described on Linkedin Education section')


class NoEducationException(Exception):
    def __init__(self):
        Exception.__init__(self, 'Linkedin Education empty on profile')

        
class NoAssignedStartupException(Exception):
    def __init__(self):
        Exception.__init__(self, 'No startup assigned to founder in table')

                
class NoEmployeeListException(Exception):
    def __init__(self):
        Exception.__init__(self, 'No employee list available for startup')

class InvalidEmployeeListException(Exception):
    def __init__(self):
        Exception.__init__(self, 'Invalid or Empty employee list for startup')

class NoExperienceException(Exception):
    def __init__(self):
        Exception.__init__(self, 'Linkedin Experience empty on profile')

