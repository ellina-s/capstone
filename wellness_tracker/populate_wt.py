import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')

import django
django.setup()

from wt.models import *


def populate():



#start popluation


    
    
    #doesn work lolz since it chnages each of these time to todays date...
    add_data(value=1000, date='2014-1-12 04:12:34', patient=User(2), question=Question(1) )
   # add_data(value=1500, date='2014-10-13 04:12:35', patient=User(2), question=Question(1) )
  # add_data(value=1300, date='2014-10-14 04:12:34', patient=User(2), question=Question(1) )
  #  add_data(value=2500, date='2014-10-15 04:12:34', patient=User(2), question=Question(1) )
   # add_data(value=2200, date='2014-10-16 04:12:34', patient=User(2), question=Question(1) )
    #add_data(value=1800, date='2014-10-17 04:12:34', patient=User(2), question=Question(1) )
    #add_data(value=2800, date='2014-10-18 04:12:34', patient=User(2), question=Question(1) )
    #add_data(value=2900, date='2014-10-19 04:12:34', patient=User(2), question=Question(1) )
    #add_data(value=3200, date='2014-10-20 04:12:34', patient=User(2), question=Question(1) )
    #add_data(value=3500, date='2014-10-21 04:12:34', patient=User(2), question=Question(1) )
    #add_data(value=3100, date='2014-10-22 04:12:34', patient=User(2), question=Question(1) )
    #add_data(value=2900, date='2014-10-23 04:12:34', patient=User(2), question=Question(1) )



    

    # Print out what we have added to the user.
   # for c in Category.objects.all():
       # for p in Page.objects.filter(category=c):
           # print "- {0} - {1}".format(str(c), str(p))

def add_data(value, date, patient, question, comment="empty"):
    p = Answer.objects.get_or_create(value=value, date=date, patient=patient, question=question, comment=comment)[0]
    return p



# Start execution here!
if __name__ == '__main__':
    print "Starting Wellnesstracker population script..."
    populate()
