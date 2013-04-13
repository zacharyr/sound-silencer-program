 Sound Silencer Program
====================

<ul>
<li>Sound Silencer is a simple python program designed to silence all background noises on keystroke, so that you can peacefully talk on your microphone.</li>
<li>Once you launch the program, you will be required to set a keyboard key to be the default 'silencing' key' or the key that will be used to toggle your computer's sound. Once you set the key, launch the sound silencing script.</li>
</ul>

<h2>Making it Executable</h2>

Those who wish to download an executable, I have provided the EXE in the repository, just look up top. Those who wish to compile the code to an EXE themselves, look below.

<ol>
<li>Download and install the dependencies: <a title="Python" href="http://www.python.org/download/">Python</a>, <a title="PyInstaller" href="http://www.pyinstaller.org/">PyInstaller</a>, <a title="PyWin32" href="http://sourceforge.net/projects/pywin32/files/">PyWin32</a>, and <a title="wxPython" href="http://www.wxpython.org/download.php">wxPython</a> if you have not already installed it.</li>
<li>After you downloaded and installed the previous packages, run the following command in your python terminal: <code>python pyinstaller/utils/Makespec.py --onefile --noconsole sound_silencer.py</code>
<li>This will generate a 'spec' file, which you will now use with Build.py to compile an .EXE: <code>python pyinstaller/utils/Build.py pyinstaller\pyinstaller.spec</code></li>
<li>Running the previous command will create a single file executable which you can place on a computer that does or even does not have python installed.</li>
</ol>

<h2>Authors</h2>
<a title="Zach Rohde" href="http://zachrohde.com">Zach Rohde</a>