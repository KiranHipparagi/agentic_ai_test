import zipfile
import xml.etree.ElementTree as ET
import sys
import os

def read_docx(file_path):
    try:
        with zipfile.ZipFile(file_path) as docx:
            xml_content = docx.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            
            # XML namespaces in Word
            namespaces = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            }
            
            text = []
            for paragraph in tree.iterfind('.//w:p', namespaces):
                p_text = []
                for node in paragraph.iterfind('.//w:t', namespaces):
                    if node.text:
                        p_text.append(node.text)
                if p_text:
                    text.append(''.join(p_text))
            
            return '\n'.join(text)
    except Exception as e:
        return f"Error reading .docx: {str(e)}"

if __name__ == "__main__":
    # Adjust path as needed
    path = r"c:\Users\Bharat Computers\Desktop\gihub-projects\Agentinc_AI\New logic.docx"
    if os.path.exists(path):
        print(read_docx(path))
    else:
        print(f"File not found: {path}")
