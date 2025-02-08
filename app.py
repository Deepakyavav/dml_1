import streamlit as st
from streamlit_ace import st_ace
import streamlit.components.v1 as components
import os
import re
import glob
import markdown
import base64
from pathlib import Path
import importlib.util
import sys
from io import StringIO
import contextlib
# Constants
PROBLEMS_DIR = "Problems"
SUPPORTED_EXTENSIONS = ['.md', '.html', '.py']

def setup_page():
    """Configure the Streamlit page settings"""
    st.set_page_config(
        page_title="DML-OpenProblem Interactive Platform",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("DML-OpenProblem Interactive Platform")

def get_problem_directories():
    """Get all problem directories sorted numerically"""
    problem_dirs = [d for d in os.listdir(PROBLEMS_DIR) 
                   if os.path.isdir(os.path.join(PROBLEMS_DIR, d))]
    
    # Sort directories numerically when possible
    def get_number(dirname):
        match = re.match(r'(\d+)_', dirname)
        return int(match.group(1)) if match else float('inf')
    
    return sorted(problem_dirs, key=get_number)

def load_file_content(file_path):
    """Load and return file content with proper encoding"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return ""

def save_file_content(file_path, content):
    """Save content to file with proper encoding"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        st.success(f"Successfully saved changes to {file_path}")
    except Exception as e:
        st.error(f"Error saving file: {e}")

def render_math_content(content, file_ext):
    """Render content with MathJax support"""
    if file_ext == '.md':
        content = markdown.markdown(content)
    
    # Replace LaTeX delimiters
    content = re.sub(r'\\\(', r'$', content)
    content = re.sub(r'\\\)', r'$', content)
    content = re.sub(r'\\\[', r'$$', content)
    content = re.sub(r'\\\]', r'$$', content)
    
    return components.html(
        f"""
        <div style="padding: 20px;">
            {content}
        </div>
        <script>
            window.MathJax = {{
                tex: {{
                    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
                }},
                svg: {{
                    fontCache: 'global'
                }}
            }};
        </script>
        <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        """,
        height=600,
        scrolling=True
    )

def create_new_problem():
    """Interface for creating a new problem"""
    st.subheader("Create New Problem")
    
    col1, col2 = st.columns(2)
    with col1:
        problem_number = st.number_input("Problem Number", min_value=1, step=1)
        problem_name = st.text_input("Problem Name")
    
    if st.button("Create Problem"):
        if problem_number and problem_name:
            dir_name = f"{problem_number}_{problem_name.replace(' ', '_')}"
            problem_path = os.path.join(PROBLEMS_DIR, dir_name)
            
            try:
                os.makedirs(problem_path, exist_ok=True)
                # Create template files
                with open(os.path.join(problem_path, 'learn.md'), 'w') as f:
                    f.write("# Problem Description\n\n## Overview\n\n## Examples\n")
                with open(os.path.join(problem_path, 'solution.py'), 'w') as f:
                    f.write("def solution():\n    pass\n\n# Test cases\n")
                
                st.success(f"Created new problem: {dir_name}")
            except Exception as e:
                st.error(f"Error creating problem: {e}")





def execute_notebook(notebook_path):
    """
    Safely execute a notebook.py file and capture its output
    """
    try:
        # Create a spec for the module
        spec = importlib.util.spec_from_file_location("notebook_module", notebook_path)
        if spec is None:
            raise ImportError(f"Could not load spec for {notebook_path}")
            
        # Create the module
        module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise ImportError(f"Could not load module for {notebook_path}")
            
        # Add the module to sys.modules
        sys.modules["notebook_module"] = module
        
        # Execute the module
        buffer = StringIO()
        with contextlib.redirect_stdout(buffer):
            spec.loader.exec_module(module)
            
        return buffer.getvalue()
        
    except Exception as e:
        raise Exception(f"Error executing notebook: {str(e)}")




def main():
    setup_page()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Problem Browser", "Create New Problem", "Interactive Learn"]
    )
    
    if page == "Problem Browser":
        # Get problem directories
        problem_dirs = get_problem_directories()
        
        # Problem selection
        selected_problem = st.sidebar.selectbox(
            "Select Problem",
            problem_dirs
        )
        
        if selected_problem:
            problem_path = os.path.join(PROBLEMS_DIR, selected_problem)
            
            # File selection
            files = [f for f in os.listdir(problem_path) 
                    if os.path.splitext(f)[1] in SUPPORTED_EXTENSIONS]
            selected_file = st.sidebar.selectbox(
                "Select File",
                files
            )
            
            if selected_file:
                file_path = os.path.join(problem_path, selected_file)
                file_ext = os.path.splitext(selected_file)[1]
                
                # Main content area
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Editor")
                    content = load_file_content(file_path)
                    
                    # Determine language for the editor
                    lang_map = {'.py': 'python', '.md': 'markdown', '.html': 'html'}
                    editor_lang = lang_map.get(file_ext, 'text')
                    
                    edited_content = st_ace(
                        value=content,
                        language=editor_lang,
                        theme="monokai",
                        key=f"editor_{selected_file}",
                        height=500
                    )
                    
                    if st.button("Save Changes"):
                        save_file_content(file_path, edited_content)
                
                with col2:
                    st.subheader("Preview")
                    if file_ext in ['.md', '.html']:
                        render_math_content(edited_content, file_ext)
                    elif file_ext == '.py':
                        st.code(edited_content, language='python')
    
    elif page == "Create New Problem":
        create_new_problem()
    

    elif page == "Interactive Learn":
        st.subheader("Interactive Learning Platform")
        
        # Get interactive learn directories
        learn_dirs = glob.glob(os.path.join(PROBLEMS_DIR, "interactive_learn", "problem-*"))
        
        selected_learn = st.sidebar.selectbox(
            "Select Interactive Problem",
            [os.path.basename(d) for d in learn_dirs]
        )
        
        if selected_learn:
            notebook_path = os.path.join(PROBLEMS_DIR, "interactive_learn", selected_learn, "notebook.py")
            if os.path.exists(notebook_path):
                # Show the notebook content
                content = load_file_content(notebook_path)
                with st.expander("View Notebook Code"):
                    st.code(content, language='python')
                
                # Add execution controls
                if st.button("Run Notebook"):
                    try:
                        with st.spinner("Executing notebook..."):
                            output = execute_notebook(notebook_path)
                            st.success("Notebook executed successfully!")
                            
                            # Show output in an expander
                            with st.expander("Execution Output"):
                                st.text(output)
                                
                    except Exception as e:
                        st.error(f"Error executing notebook: {str(e)}")
                        st.info("Make sure the notebook.py file contains valid Python code and required dependencies are installed.")
            else:
                st.warning(f"No notebook.py file found in {selected_learn}")
if __name__ == "__main__":
    main()