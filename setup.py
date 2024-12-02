from setuptools import setup,find_packages

setup(
    name               = 'azvcutter'
    , version          = '1.12012024.1'
    , license          = 'MIT'
    , author           = "Andrew Zhu"
    , author_email     = 'xhinker@hotmail.com'
    , packages         = find_packages('src')
    , package_dir      = {'': 'src'}
    , url              = 'https://github.com/xhinker/azvcutter'
    , keywords         = 'NVidia GPU, Video Editor, Python'
    , install_requires = [
        ""
    ]
    , include_package_data=True
)