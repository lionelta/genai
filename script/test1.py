#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.11.1_ipython/bin/python



from docx import Document

def update_image_descriptions(docx_file):
    """
    Updates the description (descr) metadata of images in a .docx file
    to their respective relationship target names.

    Args:
        docx_file (str): The path to the Word document (.docx).
    """
    try:
        # Open the document
        doc = Document(docx_file)

        # Iterate through all the parts of the document
        for part in doc.part.package.parts:
            # Check if the part is a document relationship part
            if part.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml':
                # Iterate through all relationships in the main document part
                for r in part.relationships.values():
                    # Check if the relationship is an image
                    if r.target_ref.startswith('media/'):
                        try:
                            # Get the image object
                            image = r.target_part.blob

                            # Find the image shape in the document
                            for p in doc.paragraphs:
                                for run in p.runs:
                                    for inline in run.element.xpath('.//a:blip'):
                                        # Get the relationship ID of the inline image
                                        r_id = inline.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')

                                        # Check if this is our image
                                        if r_id == r.rId:
                                            # Get the parent of the blip, which is usually the 'graphicData'
                                            graphic_data = inline.getparent().getparent()

                                            # Find the 'cNvPr' element (common properties)
                                            cNvPr = graphic_data.find('.//a:cNvPr')
                                            if cNvPr is not None:
                                                # Update the description (descr) attribute
                                                cNvPr.set('descr', r.target_ref)
                                                print(f"Updated description for image with relationship ID '{r.rId}' to '{r.target_ref}'")

                        except Exception as e:
                            print(f"Could not process image relationship '{r.rId}': {e}")
            
        # Save the modified document
        doc.save(docx_file)
        print("Document updated successfully!")

    except FileNotFoundError:
        print(f"Error: The file '{docx_file}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Example usage:
if __name__ == '__main__':
    # Replace 'your_document.docx' with the path to your file
    import sys
    file_path = sys.argv[1]
    update_image_descriptions(file_path)


