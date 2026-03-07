import json 
import os 
from glob import glob 

class FontManager :
    def __init__ (self ,fonts_file ='fonts.json',fonts_dir ='fonts'):
        self .fonts_file =fonts_file 
        self .fonts_dir =fonts_dir 
        self .fonts ={}
        self .current_font_name ="DejaVu Sans"
        self .current_font ={}
        self .load_fonts ()

    def load_fonts (self ):
        try :
            if os .path .exists (self .fonts_file ):
                with open (self .fonts_file ,'r')as f :
                    data =json .load (f )
                    self .fonts =data .get ('fonts',{})
                    self .current_font_name =data .get ('current_font','DejaVu Sans')
            else :

                self .fonts =self ._get_default_fonts ()
                self .current_font_name ='DejaVu Sans'
                self .save_fonts ()

            self ._scan_fonts_directory ()

            if self .current_font_name in self .fonts :
                self .current_font =self .fonts [self .current_font_name ]
            else :
                self .current_font =self .fonts .get ('DejaVu Sans',{})
                self .current_font_name ='DejaVu Sans'
        except Exception as e :
            print (f"Error loading fonts: {e }")
            self .fonts =self ._get_default_fonts ()
            self .current_font =self .fonts ['DejaVu Sans']
            self .current_font_name ='DejaVu Sans'

    def _scan_fonts_directory (self ):
        try :
            fonts_path =os .path .join (os .path .dirname (__file__ ),self .fonts_dir )
            if os .path .exists (fonts_path ):

                ttf_files =glob (os .path .join (fonts_path ,'*.ttf'))
                otf_files =glob (os .path .join (fonts_path ,'*.otf'))
                all_fonts =ttf_files +otf_files 

                for font_path in all_fonts :
                    font_filename =os .path .basename (font_path )

                    font_name =os .path .splitext (font_filename )[0 ].replace ('-',' ').replace ('_',' ')

                    if font_name not in self .fonts :
                        self .fonts [font_name ]={
                        'name':font_name ,
                        'path':font_filename ,
                        'regular':font_filename ,
                        'bold':font_filename 
                        }
        except Exception as e :
            print (f"Error scanning fonts directory: {e }")

    def save_fonts (self ):
        try :
            data ={
            'fonts':self .fonts ,
            'current_font':self .current_font_name 
            }
            with open (self .fonts_file ,'w')as f :
                json .dump (data ,f ,indent =2 )
        except Exception as e :
            print (f"Error saving fonts: {e }")

    def set_font (self ,font_name ):
        if font_name in self .fonts :
            self .current_font_name =font_name 
            self .current_font =self .fonts [font_name ]
            self .save_fonts ()
            return True 
        return False 

    def get_font_names (self ):
        return list (self .fonts .keys ())

    def get_font_path (self ,style ='regular'):
        font_key ='bold'if style =='bold'else 'regular'
        font_filename =self .current_font .get (font_key ,self .current_font .get ('path','DejaVuSans.ttf'))

        bundled_path =os .path .join (os .path .dirname (__file__ ),self .fonts_dir ,font_filename )
        if os .path .exists (bundled_path ):
            return bundled_path 

        system_paths =[
        f"/usr/share/fonts/truetype/dejavu/{font_filename }",
        f"/usr/share/fonts/truetype/{font_filename }",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

        for path in system_paths :
            if os .path .exists (path ):
                return path 

        return bundled_path 

    def _get_default_fonts (self ):
        return {
        "DejaVu Sans":{
        "name":"DejaVu Sans",
        "path":"DejaVuSans.ttf",
        "regular":"DejaVuSans.ttf",
        "bold":"DejaVuSans-Bold.ttf"
        },
        "DejaVu Sans Bold":{
        "name":"DejaVu Sans Bold",
        "path":"DejaVuSans-Bold.ttf",
        "regular":"DejaVuSans-Bold.ttf",
        "bold":"DejaVuSans-Bold.ttf"
        }
        }

    def get_current_font_name (self ):
        return self .current_font_name 
