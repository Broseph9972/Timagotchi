
import sys 
import time 

try :
    from display_waveshare import WaveshareDisplay 
    from input_handler import InputHandler 
    from menu import Menu 
    from theme_manager import ThemeManager 

    print ("Starting Pi Schedule Display...")


    theme_manager =ThemeManager ()


    display =WaveshareDisplay (theme_manager )
    print ("Display initialized")

    input_handler =InputHandler ()
    print ("Input handler initialized")

    menu =Menu (display ,input_handler )
    print ("Menu system ready")


    print ("Starting background git maintenance...")
    menu .start_boot_git_maintenance_background ()



    try :
        ready_file ='/tmp/timagotchi_ready'
        with open (ready_file ,'w')as f :
            f .write ('1')
        print ("Sent ready signal to splash screen")
    except Exception as e :
        print (f"Warning: Could not write ready signal: {e }")

    menu .run ()

    print ("Exiting...")
    display .clear ()

except KeyboardInterrupt :
    print ("\nExiting on keyboard interrupt...")
    sys .exit (0 )
except Exception as e :
    print (f"Error: {e }")
    import traceback 
    traceback .print_exc ()
    sys .exit (1 )
