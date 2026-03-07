
import sys 
import time 

try :
    from display_waveshare import WaveshareDisplay 
except Exception as e :
    print ("Failed to import display driver:",e )
    sys .exit (1 )

try :
    from input_handler import InputHandler 
except Exception :
    InputHandler =None 

from menu import Menu 

class DummyInput :
    def get_input (self ):
        return None 
    def cleanup (self ):
        pass 

def main ():
    try :
        display =WaveshareDisplay ()
    except Exception as e :
        print ("Display initialization failed:",e )
        sys .exit (1 )

    if InputHandler is not None :
        try :
            input_handler =InputHandler ()
        except Exception :
            input_handler =DummyInput ()
    else :
        input_handler =DummyInput ()

    menu =Menu (display ,input_handler )
    menu .current_screen ="schedule"

    print ("Quick schedule display started. Press Ctrl+C to exit.")

    try :
        while True :
            menu .show_schedule_screen ()
            time .sleep (1 )
    except KeyboardInterrupt :
        print ("Exiting quick schedule display...")
    finally :
        try :
            display .clear ()
        except Exception :
            pass 
        try :
            input_handler .cleanup ()
        except Exception :
            pass 

if __name__ =="__main__":
    main ()
