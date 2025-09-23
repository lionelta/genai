#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python


import os
import sys
import logging
import argparse
import zipfile
import os

def main(args):
    extract_images_from_docx(args.infile, args.outdir)

def extract_images_from_docx(docx_path, output_dir):
    """
    Extracts images from a .docx file and saves them to a specified directory.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        with zipfile.ZipFile(docx_path, 'r') as zip_ref:
            # Get a list of all files in the zip archive
            all_files = zip_ref.namelist()

            # Filter for image files
            image_files = [f for f in all_files if f.startswith('word/media/') and f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.emf'))]

            for image_path in image_files:
                # Get the filename and create the full output path
                filename = os.path.basename(image_path)
                output_path = os.path.join(output_dir, filename)

                # Extract the image file to the output directory
                with open(output_path, 'wb') as output_file:
                    output_file.write(zip_ref.read(image_path))
                
                # Convert emf files to png, and then delete it
                if image_path.lower().endswith('.emf'):
                    png_output_path = output_path[:-4] + '.jpg'
                    os.system(f'unoconv -f jpg -o {png_output_path} {output_path}')
                    os.remove(output_path)
            
    except zipfile.BadZipFile:
        print(f"Error: {docx_path} is not a valid zip file.")



if __name__ == '__main__':
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog=os.path.basename(__file__), formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('--infile', default=None, required=True, help='input file')
    parser.add_argument('--outdir', default=None, required=True, help='output directory for extracted images')
    args = parser.parse_args()

    main(args)

