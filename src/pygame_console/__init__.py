'''
	Implementation of graphical in-game console
	supporting input and output in graphics (pygame)

	Features
	********
		-	command buffer on text input
		-	buffer on text output and scrolling up and down in it (pgUp, pgDown) and/or mouse wheel
		-	console transparent background
		-	picture as a console background
		-	animation of showing/hiding console in the game
		-	console header and footer
		-	transparent header, output, input - by implementing show function in header, textoutput etc
		-	header and footer can display dynamic data from app reference - time, position, fps, ...
		-	possibility to run scripts
		-	support for colors in console (+ commands are stored in input color on the output)
		-	updated help for the commands
		-	breaking the text in text output - support big outputs		
		-	cutting the text of text input
		-	text input is not limited and scrolls automatically to the left.
		-	in text input fix jumping text line when '1' or 'q' is input - this is the best solution, use different font if not satisfied
		-	console does not ne!ed to contain header/footer/input/output - based on json config
		-	commands implemented as custom modules
		-	console scripts supported in specified directory
		-	console can be reloaded after the change of configuration
		- 	console scripts are now supporting parameters, for example `script example3.scr x=100 y=500 color=128 name=MyBrick`
		-	tabs are now translated to spaces based on tab_spaces parameter


	FEATURES TODO
	*************

		-	Customize keys for console via json configuration
		-	Show optional vertical scroll bar on console output



	How to incorporate in the code
	******************************
		-	create console instance in the main class/module - reference to main/module
		-	add game.console_enabled property to the game instance
		-	in the main game loop test if console key was pressed - if yes, game.console_enabled = True
		-	if game.console_enabled = True then after generating game screen, generate also console screen
		-	show_amim_console for animated spawn in main game class
'''

from io import StringIO # for redirection of commands output to the graphical console
from pathlib import Path
import sys	# for redirection of stdout to the graphical console
import pygame # for Surface and graphics init
import pygame.freetype # for all the fonts
import pygame.locals as pl # for key names
import cmd	# for command line support https://docs.python.org/3/library/cmd.html

# Utils functions
from importlib import import_module

def str_to_package_module(package: str, module: str):
    '''Gets reference to the module in the package

    Parameters:
        :param package: Path to the package, for example pyrpg.core.ecs
        :type package: str

        :param module: Path to the module, relative to the package
        :type module: str
    '''
    try:
        return import_module(module, package=package)
    except ModuleNotFoundError:
        raise ValueError(f'Incorrect package.module name "{package}.{module}"')


class Padding(tuple):
	''' Class to facilitate easier and more understandable work 
	with console paddings that are tuples (indexing). Items of this class
	can be accessed by either indexing or by name.

	e.g. 
		pad = Padding((1,2,3,4))	
		pad[0] returns 1
		pad.up returns also 1
	'''

	def __init__(self, padding=(0,0,0,0)):
		''' Init the padding and translate the tupple into 
		readable padding properties.
		'''

		# Missing values during initiation are substituted by 0
		self.up = padding[0] if len(padding) > 0 else 0
		self.down = padding[1] if len(padding) > 1 else 0
		self.left = padding[2] if len(padding) > 2 else 0
		self.right = padding[3] if len(padding) > 3 else 0

class CommandLineProcessor(cmd.Cmd):
	''' Class implementing the logic behind console commands.
	Code was taken, modified and adjsuted from original Tuxemon game 
	https://github.com/Tuxemon/Tuxemon
	'''

	def __init__(self, app, input=sys.stdin, output=sys.stdout, cmd_pckg_path=None, script_path=None):
		''' Inherit from Cmd class. Output will need to be redirected 
		to console graphical output, otherwise it would go to the text
		window.
		'''

		# Initiate the parent class
		cmd.Cmd.__init__(self, stdin=input, stdout=output)
		self.app = app
		self.output = output
		self.input = input
		self.cmd_pckg_path = cmd_pckg_path # the package containing modules implementing console commands
		self.script_path = script_path # the path to the directory with console scripts
		self._cmd_scripts = dict() # dict with functions implementing commands

	def get_command(self, command_name: str):    
		'''Gets the py script module from the storage if registered or register it first.
		'''
		command_fnc = self._cmd_scripts.get(command_name)
		return command_fnc if command_fnc is not None else self.register_command(command_name)

	def register_command(self, command_module_name: str):
		'''Register the py script module.'''

		command_module_path_absolute = f"{self.cmd_pckg_path}.{command_module_name}"

		# Try to find the  module and get its reference
		try:
			command_module = str_to_package_module(None, command_module_path_absolute)

		except ValueError:
			raise ValueError(f'Error during loading of py script command module "{command_module_path_absolute}".')

		# Try to register the script
		try:
			command_module.initialize(self._register_command, command_module_name)

		except ValueError:
			raise ValueError(f'Error during initiating/registering of command module "{command_module_path_absolute}".')

		return self._cmd_scripts.get(command_module_name)

	def _register_command(self, fnc, alias) -> None:
		'''Registers new script command under some
		specific name.
		'''
		self._cmd_scripts.update({alias: fnc})

	def emptyline(self):
		''' In case empty line is entered, nothing happens
		'''
		pass

	def default(self, line):
		''' Overridden from Cmd super-class. 
		It is called always when the do_xxx function is not found.

		Parameter line contains the whole input string.

		It is the same as using 'py_script'
		'''
		self.do_py_script(line)

	def do_list(self, params):
		'''List of all commands'''
		self.output.write(f'Registered commands: {self._cmd_scripts.keys()}')
		self.output.write(f'See the {self.cmd_pckg_path} package for list of all scripted commands')

	
	def do_EOF(self, params):
		'''If you press CTRL-D on the command line, set the app's exit variable to True.
		'''
		return self.do_py_script('exit')

	def do_shell(self, params):
		''' Executes python commands in the console. App entity can be accessed
		by referencing self. See examples of possible usage below:
		 
		 - !print('Hello world') ... prints Hello World at the console
		 - !game ... prints reference to main game instance TestObject
		 - !game.pos = [200, 200] ... assignes new position to the game rect
		 - !game.surf.fill((0,0,0)) ... changes the color of the game rect to black
		 - !game.console.padding = (20,20,20,20) ... changes padding on the console
		'''
		
		console_out = sys.stdout = StringIO()

		globals_param = {'__buildins__' : None}
		
		# Here you can name the reference to game object that is used. 
		# For example 'app', 'engine', 'game', ...
		locals_param = {'game' : self.app}
		
		Result = None

		try:
			exec('Result = ' + params, globals_param, locals_param)
			Result = locals_param.get('Result')
		except Exception as E:
			self.output.write(str(E))
			return -1
		finally:
			self.output.write(str(console_out.getvalue()))
			if Result: self.output.write(str(Result))
			sys.stdout = sys.__stdout__

	def do_py_script(self, params):
		''' Executes python script

			Examples: 
				py_script test_script.py AmmoPack
		'''
		# Prepare the text output buffer
		console_out = sys.stdout = StringIO()

		try:
			py_script = self.get_command(params.split()[0]) # try to get the py script name
			py_script(game_ctx=self.app, params=params) # call the script
			self.output.write(str(console_out.getvalue())) # write anything to the console
		except Exception as E:
			#self.output.write(str(console_out.getvalue()))
			self.output.write(str(E))
			return -1
		finally:
			sys.stdout = sys.__stdout__ # restore the output buffer to original system output


	def do_script(self, params):
		''' Run custom scripts that contain commands implemented in this class.

		Script example:
			move 300 300
			!print('I have moved the brick')
			!game.surf.fill((0,0,0))
			!print('I have colored the brick')
		'''
		
		instructions = """
			Examples of usage:
				"script example1.scr"           ... runs script example1.scr
				"script example1.scr -v"        ... runs script example1.scr in verbose mode
				"script example1.scr --verbose" ... runs script example1.scr in verbose mode
				"script example3.scr x=50 y=100 name=MyBrick color=128 --verbose" ... runs script example3.scr with parameters in verbose mode
				"script -h"      ... get usage instructions
				"script --help"  ... get usage instructions
		"""


		script_line = None
		script_line_no = None
		error = None

		all_params = params.split()
		no_of_params = len(all_params)
		
		# no parameter or help
		if no_of_params == 0 or all_params[-1] in ['-h', '--help']: 
			print(instructions)
			return

		script_name = all_params[0]
		script_params = all_params[1:]
		verbose_mode = True if all_params[-1] in ['-v', '--verbose'] else False

		script_path = Path(self.script_path) / script_name

		# Prepare the dictionary with the parameters
		params_list = [s for s in all_params if s.find('=') >=0]
		params_dict = dict() # empty dictionary where script parameters will be stored as key, value pair
		for param in params_list:
			param_key, param_value = param.split('=')
			params_dict[param_key] = param_value

		# Debugs
		#(f'{all_params=}\n{no_of_params=}\n{script_name=}\n{script_params=}\n{verbose_mode=}\n{script_path=}\n{params_list=}\n{params_dict=}')

		try:
			# Open script file
			with open(script_path) as f:
				# For each line execute self.onecmd(line)
				if verbose_mode: self.output.write('>S>Script ' + script_path + ' started.')

				script_line = f.readline()
				script_line_no = 1

				while script_line:
					
					# Substitute the parameters in the particular command in the script (look for the $key in the params_dict)
					# and substitute it with the value.
					cmd_line = script_line.strip()
					
					# Replace all the keys found in the params_dict
					for param_key, param_value in params_dict.items():
						cmd_line = cmd_line.replace(f'${param_key}', param_value)

					# Execute the command, now when all parameters are substituted with their values
					#print(f'About to execute following cmd: {cmd_line=}')
					error = self.onecmd(cmd_line)
					if error: raise
					else: script_line = f.readline()
			
			# Inform that script has ended
			if verbose_mode: self.output.write('>S>Script finished successfully.')
			return None

		except FileNotFoundError:
			self.output.write('Script file "' + str(script_path) + '" not found.')
			return -1
		except:
			if not script_line: 
				self.output.write('Error loading script file "' + str(script_path) + '".')
			else:
				self.output.write('Error (' + str(error) + ') on line '+ str(script_line_no) + '. Command: ' + str(script_line.strip()))
			return -1


class Header:
	''' Class specifying properties of Console header and/or footer.
	It supports different one-line text features, such as scrolling 
	and displaying dynamic data by passing function results.
	'''

	# List of available layouts for the header. If error, TEXT_LEFT is used as default.
	LAYOUTS = [ 'TEXT_LEFT', 'TEXT_RIGHT', 'TEXT_CENTRE', 'SCROLL_LEFT', 'SCROLL_RIGHT', 
				'SCROLL_LEFT_CONTINUOUS', 'SCROLL_RIGHT_CONTINUOUS']

	def __init__(self, console, width, config={}):
		'''
		:param console: Reference to the parrent instance of Console class
		:param width: Required width of the header. It is usually determined by Console instance at the time of console init.  
		:param config: Dictionary storing all the configs necessary for correct display of header. See keys explanation below:

			text: (optional, default '') Text displayed in the header. Can contain dynamic data by referencing {}. 
				Function for dynamic data are contained in text_params list. See further.
			text_params: (optional, default []) List of functions that are mapped to {} in text parameters. Defines module and function as a list.
			layout (optional, default ['TEXT_LEFT']): Specifies formating of the text in the header. List contains 3 parameters. Second and third parameters
				are optional. First param specifies layout. Second specifies time in ms for scrolling text. Third param specifies
				movement speed in pixels.
			padding (optional, default (0,0,0,0)): Specifies padding between header borders and text in the header. The padding order is UP, DOWN, LEFT, RIGHT
			font_file (mandatory): Path to the font file
			font_size (optional, default 12): Font size
			font_antialias (optional, default True): Font antialias (True/False)
			font_color (optional, default (255,255,255)): Font color as tuple with 3 values. Eg. (255,255,255) for white.
			font_bck_color (optional, default None): Font text background color as tuple with 3 values. Eg. (255,255,255) for white.
			bck_color (optional, default (0,0,0)): Color of the header background as tuple with 3 values.  Eg. (255,255,255) for white.
			bck_image (optional, default None): Path to image displayed on the Header background.
			bck_image_resize (optional, default True): True/False, if image should be adjusted to header dimensions.
			bck_alpha (optional, default 255): 0-255, if header background should be transparent
		'''

		self.width = width
		self.console = console

		# Dictionary with default values
		default_config = {
					'text' : '',
					'text_params' : [],
					'layout' : ['TEXT_LEFT'],
					'padding' : (0,0,0,0),
					'font_size' : 14,
					'font_antialias' : True,
					'font_color' : (255,255,255),
					'font_bck_color' : None,
					'bck_color' : (0,0,0),
					'bck_image' : None,
					'bck_image_resize' : True,
					'bck_alpha' : 128
		}

		# Merge default values with given values - overwrite defaults by config dict
		config = {**default_config, **config}

		# Save the params from the config dict
		for key in config: setattr(self, key, config.get(key))

		# Get and translate the package-method pairs from text_params parameter
		try:
			tmp_text_params = []
			for pack_method in self.text_params: # iterate list of pack-method values
				package, method = pack_method
				package = sys.modules[package] if package is not None else self.console.app # if package is not specified use the console CLI app
				tmp_text_params.append([package, method])
			self.text_params = tmp_text_params
		except AttributeError:
			# if self.text_params are not defined, continue
			pass


		# Instantiate padding for further use
		self.padding = Padding(self.padding)

		''' Layout related params (scrolling) 
		'''
		self.layout_name = self.layout[0] if len(self.layout) > 0 and self.layout[0] in Header.LAYOUTS else 'TEXT_LEFT'
		self.scroll_last_time = pygame.time.get_ticks()
		self.scroll_offset = 0
		self.scroll_offset_speed_ms = self.layout[1] if len(self.layout) > 1 else 1
		self.scroll_offset_speed_px = self.layout[2] if len(self.layout) > 2 else 1

		''' Font and surface related params
			*******************************
			- surf ... basic surface of header, footer, input and output
			- surf_dim ... dimension (Rect) of the basic surface 
			- txt_surf ... surface to display text, applies padding to surface, cuts the text. It is transparent. and 
			               it is blitted to the main surface
			- txt_surf_dim ... dimension (Rect) of the text surface
			- fnt_txt_surf ... surface for displaying front font text. It is being blitted to txt_surf in order to cut
								the text so it does not cross the console borders
			- fnt_txt_surf_dim ... dimension (Rect) of the front font end surface
			- fnt_bck_surf ... surface for displaying backgound of the font text. It is being blitted to txt_surf in order to cut
								the text so it does not cross the console borders
			- fnt_bck_surf_dim ... dimensions (Rect) of the text background
		''' 

		pygame.freetype.init() 
		self.font_object = pygame.freetype.Font(str(self.font_file), self.font_size)

		# Get the height of the text font line and store it in line_spacing
		# This is necessary so that the hight of the row spacing is not
		# dynamicaly changing based on text height with TrueType fonts.
		(_, rect_tmp) = self.font_object.render('|q', self.font_color, None )
		self.line_spacing = rect_tmp.height

		#####
		# Create the main header surface
		#####
		self.surf_dim = pygame.Rect(0, 0, self.width, self.line_spacing + self.padding.up + self.padding.down)
		self.surf = pygame.Surface((int(self.surf_dim.width), int(self.surf_dim.height)))

		# Fill the header surface with background color
		self.surf.fill(self.bck_color)
		
		# Fill the surface with picture	if necessary
		if self.bck_image:
			self.bck_image = pygame.image.load(str(self.bck_image)).convert()
			if self.bck_image_resize:
				self.bck_image = pygame.transform.scale(self.bck_image, (self.surf_dim.width, self.surf_dim.height))
			
			# Blit the background picture on the header surface
			self.surf.blit(self.bck_image, (0, 0))

		# Set alpha of the header surface
		self.surf.set_alpha(self.bck_alpha)

		#####
		# Create surface for text area - necessary for proper cutting of the text
		#####
		self.txt_surf_dim = pygame.Rect(
						0,
						0,
						self.surf_dim.width - self.padding.left - self.padding.right,
						self.surf_dim.height - self.padding.up - self.padding.down
						)

		self.txt_surf = pygame.Surface(
							(self.txt_surf_dim.width, self.txt_surf_dim.height),
							pygame.SRCALPHA)
		
		#####
		# Create surface for text and store its dimensions
		#####
		(self.fnt_txt_surf, self.fnt_txt_surf_dim) = self.font_object.render(self.text, self.font_color, None)

		#####
		# Create surface for text background if needed
		#####
		if self.font_bck_color:
			self.fnt_bck_surf_dim = self.fnt_txt_surf_dim
			self.fnt_bck_surf = pygame.Surface((self.fnt_txt_surf_dim.width, self.line_spacing))
			self.fnt_bck_surf.fill(self.font_bck_color)

		#####
		# Scrolling parameters
		#####
		# How many times the text for scrolling must be blitted to create the continuation effect
		if self.layout_name in ['SCROLL_LEFT_CONTINUOUS', 'SCROLL_RIGHT_CONTINUOUS']:
			self.scroll_repeats = (self.txt_surf_dim.width // self.fnt_txt_surf_dim.width) + 2

	def update(self):
		''' Called from console update function in order to generate the dynamic
		text in the header and adjust the surface, if needed.
		'''

		# Only do something if dynamic params are needed. Otherwise, it is not necessary
		if self.text_params:
			
			# prepare the dynamic text
			try:
				text = self.text.format(*[getattr(pack_method[0], pack_method[1])() for pack_method in self.text_params])				
			except AttributeError:
				text = f"Missing function in'{self.text_params}'"

			# generate the new text in self.text_surface object
			(self.fnt_txt_surf, self.fnt_txt_surf_dim) = self.font_object.render(text, self.font_color, None )

			# How many times the text for scrolling must be blitted to create the continuation effect
			if self.layout_name in ['SCROLL_LEFT_CONTINUOUS', 'SCROLL_RIGHT_CONTINUOUS']:
				self.scroll_repeats = (self.txt_surf_dim.width // self.fnt_txt_surf_dim.width) + 2

	def show(self, surf, pos=(0, 0)):
		''' Blit the surfaces to the main Header surface (surf).
		'''

		# Blit the main header surface to background
		surf.blit(self.surf, (int(pos[0]), int(pos[1])) )

		# Clear the main text surface on which the actual text is blitted
		self.txt_surf.fill((0,0,0,0)) # Last 0 indicates alpha, i.e. full transparency

		if self.layout_name == 'TEXT_RIGHT':
			if self.font_bck_color: self.txt_surf.blit(self.fnt_bck_surf, (int(self.txt_surf_dim.width - self.fnt_txt_surf_dim.width), 0))
			self.txt_surf.blit(self.fnt_txt_surf, (int(self.txt_surf_dim.width - self.fnt_txt_surf_dim.width), 0))			

		if self.layout_name == 'TEXT_LEFT':
			if self.font_bck_color: self.txt_surf.blit(self.fnt_bck_surf, (0,0))
			self.txt_surf.blit(self.fnt_txt_surf, (0,0))

		if self.layout_name == 'TEXT_CENTRE':
			if self.font_bck_color: self.txt_surf.blit(self.fnt_bck_surf, (int(self.txt_surf_dim.width // 2 - self.fnt_text_surf_dim.width // 2), 0))
			self.txt_surf.blit(self.fnt_txt_surf, (int(self.txt_surf_dim.width // 2 - self.fnt_txt_surf_dim.width // 2), 0))

		if self.layout_name == 'SCROLL_LEFT':
			if self.scroll_offset > -1 * self.fnt_txt_surf_dim.width:
				self.scroll_offset = (self.scroll_offset - self.scroll_offset_speed)  
			else: 
				self.scroll_offset = self.txt_surf_dim.width

			if self.font_bck_color: self.txt_surf.blit(self.fnt_bck_surf, (int(self.scroll_offset), 0))
			self.txt_surf.blit(self.fnt_txt_surf, (int(self.scroll_offset), 0))

		if self.layout_name == 'SCROLL_RIGHT':
			if self.scroll_offset < 1 * self.txt_surf_dim.width:
				self.scroll_offset = (self.scroll_offset + self.scroll_offset_speed)
			else: 
				self.scroll_offset = -1 * self.fnt_txt_surf_dim.width

			if self.font_bck_color: self.txt_surf.blit(self.fnt_bck_surf, (int(self.scroll_offset), 0))
			self.txt_surf.blit(self.fnt_txt_surf, (int(self.scroll_offset), 0))

		if self.layout_name == 'SCROLL_LEFT_CONTINUOUS':

			# If the time for scrolling comes
			current_time = pygame.time.get_ticks()

			# Calculate how much time has passed since last time (ms)
			delay = current_time - self.scroll_last_time

			if delay >= self.scroll_offset_speed_ms:
				
				# Reset the scrolling time check
				self.scroll_last_time = current_time
				
				# Increase the offset by given number of pixels
				self.scroll_offset = (self.scroll_offset - self.scroll_offset_speed_px)

				# Check if scrolling needs to be reset and reset if necessary
				if self.scroll_offset < -1 * self.fnt_txt_surf_dim.width:
					self.scroll_offset = 0

			for i in range(self.scroll_repeats): 
				if self.font_bck_color: self.txt_surf.blit(self.fnt_bck_surf, (int(i * self.fnt_txt_surf_dim.width + self.scroll_offset), 0))
				self.txt_surf.blit(self.fnt_txt_surf, (int(i * self.fnt_txt_surf_dim.width + self.scroll_offset), 0))

		if self.layout_name == 'SCROLL_RIGHT_CONTINUOUS':

			# If the time for scrolling comes
			current_time = pygame.time.get_ticks()

			# Calculate how much time has passed since last time (ms)
			delay = current_time - self.scroll_last_time

			if delay >= self.scroll_offset_speed_ms:
				
				# Reset the scrolling time check
				self.scroll_last_time = current_time
				
				# Increase the offset by given number of pixels
				self.scroll_offset = (self.scroll_offset + self.scroll_offset_speed_px)

				# Check if scrolling needs to be reset and reset if necessary
				if self.scroll_offset > self.fnt_txt_surf_dim.width:
					self.scroll_offset = 0

			for i in range(self.scroll_repeats): 
				# blit the text to the right border. Then subtract text width and blit again as many times as needed
				if self.font_bck_color: self.txt_surf.blit(self.fnt_bck_surf, (int(self.txt_surf_dim.width - (i+1) * self.fnt_txt_surf_dim.width + self.scroll_offset), 0))
				self.txt_surf.blit(self.fnt_txt_surf, (int(self.txt_surf_dim.width - (i+1) * self.fnt_txt_surf_dim.width + self.scroll_offset), 0))

		
		# Blit text surface to surf - take account text padding
		surf.blit(self.txt_surf, 
				(int(pos[0] + self.padding.left),
				int(pos[1] + self.padding.up)))

	def get_height(self):
		''' Returns hight of the header surface. Called from Console instance in order
		to construct all elements of console and display correctly.
		'''
		return self.surf_dim.height

class TextOutput:
	''' Class specifying properties of Console main text output part
	where command replies are written. It supports output history and
	scrolling throug it using PgUp and PgDown keys.
	'''

	def __init__(self, console, width, config={}):
		'''
		:param console: Reference to the parrent instance of Console class
		:param width: Required width of the text output. It is usually determined by Console instance at the time of console init.  
		:param config: Dictionary storing all the configs necessary for correct display of text output. See keys explanation below:
			
			padding (optional, default (0,0,0,0)): Specifies padding between text output borders and text. The padding order is UP, DOWN, LEFT, RIGHT
			font_file (mandatory): Path to the font file
			font_size (optional, default 12): Font size
			font_antialias (optional, default True): Font antialias (True/False)
			font_color (optional, default (255,255,255)): Font color as tuple with 3 values. Eg. (255,255,255) for white.
			font_bck_color (optional, default None): Font text background color as tuple with 3 values. Eg. (255,255,255) for white.
			bck_color (optional, default (0,0,0)): Color of the text output background as tuple with 3 values.  Eg. (255,255,255) for white.
			bck_alpha (optional, default 255): 0-255, if header background should be transparent
			prompt (optional, default ''): Characters printed on the beginning of every output line.
			buffer_size (optional, default 100): How many lines of output should be stored as history.
			display_lines (mandatory): How many lines of output should be displayed on console at the same time. Defines height of the console.
			display_columns (mandatory): After how many characters the output needs to be wrapped to the new line.
			line_spacing (optional, default None): How big line spacing should there be between text output lines.
		'''		
		# Dictionary with default values
		default_config = {
					'padding' : (0,0,0,0),
					'font_size' : 16,
					'font_antialias' : True,
					'font_color' : (255,255,255),
					'font_bck_color' : None,
					'bck_color' : (0,0,0),
					'bck_alpha' : 255,
					'prompt'	: '',
					'buffer_size': 100,
					'line_spacing': None,
					'display_columns': 500,
					'tab_spaces': 4				# substitute tabs with spaces
		}

		# Merge default values with given values - overwrite defaults by config dict
		config = {**default_config, **config}

		self.width = width
		self.console = console

		# Save the params from the config dict
		for key in config: setattr(self, key, config.get(key))

		# Instantiate padding for further use
		self.padding = Padding(self.padding)

		''' Buffer related parameters
		'''
		# Stores list of past texts
		self.buffer = []
		# Necessary for implemetation of scrolling in the output buffer (PgUp, PgDown)
		self.buffer_offset = 0	

		''' Font and surface related params - part of prepare_surface and show functions
			*******************************
			- surf ... basic surface of header, footer, input and output
			- surf_dim ... dimension (Rect) of the basic surface 
			- txt_surf ... surface to display text, applies padding to surface, cuts the text. It is transparent. and 
			               it is blitted to the main surface
			- txt_surf_dim ... dimension (Rect) of the text surface
			- fnt_txt_surf ... surface for displaying front font text. It is being blitted to txt_surf in order to cut
								the text so it does not cross the console borders
			- fnt_txt_surf_dim ... dimension (Rect) of the front font end surface
			- fnt_bck_surf ... surface for displaying backgound of the font text. It is being blitted to txt_surf in order to cut
								the text so it does not cross the console borders
			- fnt_bck_surf_dim ... dimensions (Rect) of the text background
		''' 

		pygame.freetype.init() 
		self.font_object = pygame.freetype.Font(str(self.font_file), self.font_size)

		# Get the height of the text font line and store it in line_spacing
		# This is necessary so that the hight of the row spacing is not
		# dynamicaly changing based on text height with TrueType fonts.
		if not self.line_spacing:
			(_, rect_tmp) = self.font_object.render('|q', self.font_color, None)
			self.line_spacing = rect_tmp.height

		# Create the main surface and tex_surf
		self.prepare_surface()

	def prepare_surface(self):
		''' Takes the buffer and based on the buffer offset (position) genertes output 
		lines surfaces (self.surf_lines) and surface (self.surf). Those are used in show 
		function to blit to the screen.
		'''

		# First we need to clear all the buffer surfaces
		self.surf_lines = []

		# We fill the surf_lines list with buffer lines surfaces based on buffer offset and 
		# number of lines that we want to display
		for i in range(self.buffer_offset, min([len(self.buffer), self.buffer_offset + self.display_lines])):
			# Create font object with given text and given color
			# TODO - to check if the self.prompt must be on the line below???
			(surface_line_tmp, rect_tmp) = self.font_object.render(self.prompt + self.buffer[i][0], self.buffer[i][1], None)
			self.surf_lines.append( (surface_line_tmp, rect_tmp) )

		# Calculate the dimensions of test output surface
		self.surf_dim = pygame.Rect(
									0,
									0,
									self.width,
									(self.line_spacing * len(self.surf_lines)) + self.padding.up + self.padding.down
		)

		# And create the surface from scratch again
		self.surf = pygame.Surface((self.surf_dim.width, self.surf_dim.height))

		# Fill the output surface with background color
		self.surf.fill(self.bck_color)
		
		# Set alpha of the header surface
		self.surf.set_alpha(self.bck_alpha)

		# Create background (completely transparent)
		# on which the text lines are blitted. The reason is to cut 
		# the text so that it is not going over the borders.
		# This surface's dimensions are adjusted by padding
		self.txt_surf_dim = pygame.Rect(
									0,
									0,
									self.surf_dim.width - self.padding.left - self.padding.right,
									self.surf_dim.height - self.padding.up - self.padding.down
		)

		self.txt_surf = pygame.Surface((self.txt_surf_dim.width, self.txt_surf_dim.height), pygame.SRCALPHA)

	def show(self, surf, pos=(0,0)):
		''' Blits main surface, text cut surface and all individual lines to
		the given surface.
		'''		
		
		# Blit output background
		surf.blit(self.surf, (int(pos[0]), int(pos[1])))

		# Clear the main text input surf on which the actual text is blitted
		self.txt_surf.fill((0,0,0,0)) # Last 0 indicates alpha, i.e. full transparency

		# Blit all the line surfaces to the txt_surface
		height = 0
		for i in range(len(self.surf_lines)):
			
			# Get the line surface from the list
			(fnt_txt_surf, fnt_txt_surf_dim) = self.surf_lines[i]

			# Blit font background
			if self.font_bck_color:
				fnt_bck_surf = pygame.Surface((fnt_txt_surf_dim.width, fnt_txt_surf_dim.height))
				fnt_bck_surf.fill(self.font_bck_color)
				
				self.txt_surf.blit(fnt_bck_surf,
						(0,
						int(height + self.line_spacing - (( self.line_spacing - fnt_txt_surf_dim.height) // 2) - fnt_txt_surf_dim.height)))

			self.txt_surf.blit(fnt_txt_surf, 
						(0,
						int(height + self.line_spacing - (( self.line_spacing - fnt_txt_surf_dim.height) // 2) - fnt_txt_surf_dim.height)))

			height = height + self.line_spacing
		
		# Blit text surface to surf - take account text padding
		surf.blit(self.txt_surf, 
				(int(pos[0] + self.padding.left),
				int(pos[1] + self.padding.up)))

	def update(self, events):
		''' Handles scrolling the output buffer by pressing pgUP and pgDOWN keys.
		After pressing of those keys and also RETURN key, it is necessary to run
		prepare_surface function in order to generate new surfaces.
		'''

		for event in events:
			if event.type == pygame.KEYDOWN:

				if event.key == pl.K_PAGEUP:
					self.buffer_offset = max([0, self.buffer_offset - self.display_lines])
					self.prepare_surface()

				elif event.key == pl.K_PAGEDOWN:
					self.buffer_offset = min([max([0, len(self.buffer) - self.display_lines]), self.buffer_offset + self.display_lines])
					self.prepare_surface()

				elif event.key == pl.K_RETURN:
					self.buffer_offset = max([0, len(self.buffer) - self.display_lines])
					self.prepare_surface()
			
			elif event.type == pygame.MOUSEBUTTONDOWN:

				# On mouse roll button UP - one row up
				if event.button == 4:
					self.buffer_offset = max([0, self.buffer_offset - 1])
					self.prepare_surface()

				# On mouse roll button DOWN - one row down
				elif event.button == 5:
					self.buffer_offset = min([max([0, len(self.buffer) - 1]), self.buffer_offset + 1])
					self.prepare_surface()

	def write(self, text, color=None):
		''' Handles adding output text into textoutput buffer in given color
		and shifting of the buffer.
		'''	

		# If color of the putput text is not specifically given, use predefined color
		if not color: color = self.font_color

		# Remove newline at the end
		text.rstrip()

		# Substitute tabs with predefined number of spaces
		text = text.replace('\t', self.tab_spaces * ' ') 
	
		# Based on newline character put every output line on separate row
		for text_line in text.split('\n'):
			
			# Only print if there is something to print
			if text_line:

				# How many characters can we put one one line - minimal from setup and what can fit on the screen
				self.display_columns = min(self.display_columns, self.width // self.font_object.get_metrics("_")[0][1])
				
				# Split text_line to the list of strings based on number of displayable characters
				text_line_parts = [text_line[i:i+self.display_columns] for i in range(0, len(text_line), self.display_columns)]	

				# Add every splitted string into the output buffer
				for text_line_part in text_line_parts:
					
					self.buffer.append((text_line_part, color))

					# Remove old rows from the buffer
					if len(self.buffer) > self.buffer_size:
						for i in range(1,len(self.buffer)):
							self.buffer[i-1] = self.buffer[i]
						del self.buffer[len(self.buffer)-1]
	
	def get_height(self):
		''' Returns current height of the text output surface. 
		Called from Console instance in order to construct all elements 
		of console and display correctly text input part right below current
		text output.
		'''
		return self.surf_dim.height
	
	def get_max_height(self):
		''' Returns maximum possible height of the text output surface. 
		Called from Console instance in order to define the total height
		of the console.
		'''				
		return (self.line_spacing * self.display_lines) + self.padding.up + self.padding.down

class TextInput:
	''' Copyright 2017, Silas Gyger, silasgyger@gmail.com, All rights reserved.
	Borrowed from https://github.com/Nearoo/pygame-text-input under the MIT license.

	This class lets the user input a piece of text, e.g. a name or a message.
	This class let's the user input a short, one-lines piece of text at a blinking cursor
	that can be moved using the arrow-keys. Delete, home and end work as well.

	Original above modified heavilly in order to be used with the console.	
	'''
	
	def __init__(self, console, width, config={}):
		'''
		:param console: Reference to the parrent instance of Console class
		:param width: Required width of the text input. It is usually determined by Console instance at the time of console init.
		:param config: Dictionary storing all the configs necessary for correct display of text input. See keys explanation below:

			padding (optional, default (0,0,0,0)): Specifies padding between text input borders and text itself. The padding order is UP, DOWN, LEFT, RIGHT.
			font_file (mandatory): Path to the font file.
			font_size (optional, default 12): Font size.
			font_antialias (optional, default True): Font antialias (True/False).
			font_color (optional, default (255,255,255)): Font color as tuple with 3 values. Eg. (255,255,255) for white.
			font_bck_color (optional, default None): Font text background color as tuple with 3 values. Eg. (255,255,255) for white.
			bck_color (optional, default (0,0,0)): Color of the header background as tuple with 3 values.  Eg. (255,255,255) for white.
			bck_alpha (optional, default 255): 0-255, if text input background should be transparent.
			prompt (optional, default '>'): Characters printed on the beginning of every input line.
			buffer_size (optional, default 10): How many lines of input should be stored as the history.
			max_string_length (optional, default -1 ): Allowed length of the input text.
			repeat_keys_initial_ms (optional, default 400): Time in ms before keys are repeated when held.
			repeat_keys_interval_ms (optional, default 35): Interval between key press repetition when held.
			text (optional, default ''): Initial text on the input line.
			max_input_text (optional, default 1000): Maximum amount of characters that can be entered on one line.
		'''
		
		self.width = width
		self.console = console

		# Dictionary with default values
		default_config = {
					'padding' : (0,0,0,0),
					'font_size' : 16,
					'font_antialias' : True,
					'font_color' : (255,255,255),
					'font_bck_color' : None,
					'bck_color' : (0,0,0),
					'bck_alpha' : 128,
					'prompt'	: '>',
					'buffer_size' : 10,
					'max_string_length': -1,
					'repeat_keys_initial_ms' : 400,
					'repeat_keys_interval_ms': 35,
					'text' : '',
					'max_input_text' : 1000
		}

		# Merge default values with given values - overwrite defaults by config dict
		config = {**default_config, **config}

		# Save the params 
		for key in config: setattr(self, key, config.get(key))

		# Instantiate padding for further use
		self.padding = Padding(self.padding)
		
		# TODO- revise - Vars to make keydowns repeat after user pressed a key for some time:
		self.keyrepeat_counters = {}

		# TODO - revise - cannot we use console clocks? pygame.time_get_ticks instead
		self.clock = pygame.time.Clock()

		''' Buffer related parameters
		'''
		self.buffer = []
		self.buffer_offset = 0

		''' Font and surface related params
			*******************************
			- surf ... basic surface of header, footer, input and output
			- surf_dim ... dimension (Rect) of the basic surface 
			- txt_surf ... surface to display text, applies padding to surface, cuts the text. It is transparent. and 
			               it is blitted to the main surface
			- txt_surf_dim ... dimension (Rect) of the text surface
			- cursor_surf ... surface for displaying the blinking cursor
			- cursor_surf_dim ... dimensions (Rect) of the cursor
			- fnt_txt_surf ... surface for displaying front font text. It is being blitted to txt_surf in order to cut
								the text so it does not cross the console borders
			- fnt_txt_surf_dim ... dimension (Rect) of the front font end surface
			- fnt_bck_surf ... surface for displaying backgound of the font text. It is being blitted to txt_surf in order to cut
								the text so it does not cross the console borders
			- fnt_bck_surf_dim ... dimensions (Rect) of the text background
		''' 
		pygame.freetype.init() 
		self.font_object = pygame.freetype.Font(self.font_file, self.font_size)

		# Determine automatically the hight of the row - height of '|q' string
		# This prevents the surface to change its height upon different hight of 
		# characters in input_string.
		(_, rect_tmp) = self.font_object.render('|q', self.font_color, None)
		self.line_spacing = rect_tmp.height

		#####
		# Create the main text input surface
		##### 
		self.surf_dim = pygame.Rect(0, 0, self.width, self.line_spacing + self.padding.up + self.padding.down)
		self.surf = pygame.Surface((self.surf_dim.width, self.surf_dim.height))

		# Fill the header surface with background color and set the transparency
		self.surf.fill(self.bck_color)				
		if self.bck_color: self.surf.set_alpha(self.bck_alpha)

		#####
		# Create surface for text area - necessary for proper cutting of the text
		#####
		self.txt_surf_dim = pygame.Rect(
						0,
						0,
						self.surf_dim.width - self.padding.left - self.padding.right,
						self.surf_dim.height - self.padding.up - self.padding.down
						)

		self.txt_surf = pygame.Surface(
							(self.txt_surf_dim.width, self.txt_surf_dim.height),
							pygame.SRCALPHA
							)

		#####
		# Create surface for text and store its dimensions
		#####
		(self.fnt_txt_surf, self.fnt_txt_surf_dim) = self.font_object.render(self.prompt + self.text, self.font_color, None)

		#####
		# Create surface for text background if needed
		#####
		if self.font_bck_color:
			self.fnt_bck_surf_dim = self.fnt_txt_surf_dim
			self.fnt_bck_surf = pygame.Surface((self.fnt_bck_surf_dim.width, self.line_spacing))
			self.fnt_bck_surf.fill(self.font_bck_color)

		#####
		# Create surface for the cursor + additional cursor parameters
		#####
		self.cursor_surf_dim = pygame.Rect(
							0,
							0,
							int(self.font_size / 2 + 1), 
							self.line_spacing
							)

		self.cursor_surf = pygame.Surface((self.cursor_surf_dim.width, self.cursor_surf_dim.height))
		self.cursor_surf.fill(self.font_color)

		# Additional cursor parameters
		self.cursor_position = len(self.text) # set it at the end of the input line
		self.cursor_visible = True  # used for cursor blinking
		self.cursor_switch_ms = 500  # cursor blinks every 500ms
		self.cursor_ms_counter = 0 

		# Necessary to blit cursore surface to the correct position - TODO - do we need this?? This is same rect as for text_input but it ends at the position of the cursor
		#( _ , self.cursor_rect) = self.font_object.render (self.prompt + self.text[:self.cursor_position], self.font_color, None) 
		self.cursor_blit_position = self.font_object.get_rect(self.prompt + self.text[:self.cursor_position]).width

		#####
		# Scrolling parameters
		#####		
		# Used for continuous seemless scrolling of input text if text is longer than viewable area
		self.fnt_txt_scroll_offset =  min(0, int(self.txt_surf_dim.width - self.fnt_txt_surf_dim.width - self.cursor_surf_dim.width))

	def prepare_surface(self):
		''' After some text is entered it is necessary to regenerate
		the text surfaces. This function is called from update method
		where we handle text input and modification
		'''
		
		# Re-render front and back text surface
		(self.fnt_txt_surf, self.fnt_txt_surf_dim)  = self.font_object.render(self.prompt + self.text, self.font_color, None)

		if self.font_bck_color:
			self.fnt_bck_surf_dim = self.fnt_txt_surf_dim
			self.fnt_bck_surf = pygame.Surface((self.fnt_bck_surf_dim.width, self.line_spacing))
			self.fnt_bck_surf.fill(self.font_bck_color)

		# Update scroll offset after input text is somehow modified
		self.fnt_txt_scroll_offset =  min(0, int(self.txt_surf_dim.width - self.fnt_txt_surf_dim.width - self.cursor_surf_dim.width))

	def update(self, events):
		''' Handles pressing of the keys. After the press, it is necessary to run
		prepare_surface function in order to update surfaces and their dimensions.
		'''

		#####
		# Handle Key pressed
		#####
		for event in events:
			if event.type == pygame.KEYDOWN:
				
				# If key is pressed, cursor must be ALWAYS visible so that person knows where to edit
				self.cursor_visible = True

				# If none exist, create counter for that key:
				if event.key not in self.keyrepeat_counters:
					self.keyrepeat_counters[event.key] = [0, event.unicode]

				if event.key == pl.K_BACKSPACE:
					self.text = (
						self.text[:max(self.cursor_position - 1, 0)]
						+ self.text[self.cursor_position:]
					)
					# Subtract one from cursor_pos, but do not go below zero:
					self.cursor_position = max(self.cursor_position - 1, 0)
					self.cursor_blit_position = self.font_object.get_rect(self.prompt + self.text[:self.cursor_position]).width

					# Regenerate text surfaces
					self.prepare_surface()

				elif event.key == pl.K_DELETE:
					self.text = (
						self.text[:self.cursor_position]
						+ self.text[self.cursor_position + 1:]
					)
					# Regenerate text surfaces
					self.prepare_surface()

				elif event.key in (pl.K_RETURN, pl.K_KP_ENTER): # support also enter on keypad
					# Only store if there is something to store
					if self.text:
						self.buffer.append(self.text)
						self.buffer_offset = len(self.buffer)

						# Remove old rows from the buffer
						if len(self.buffer) > self.buffer_size:
							for i in range(1,len(self.buffer)):
								self.buffer[i-1] = self.buffer[i]
							del self.buffer[len(self.buffer)-1]
							# Adjust the buffer offset to point to the last item in the list
							self.buffer_offset = len(self.buffer) - 1

					# Important to return True so that console instance knows that it must process a command
					return True

				elif event.key == pl.K_RIGHT:
					# Add one to cursor_pos, but do not exceed len(input_string)
					self.cursor_position = min(self.cursor_position + 1, len(self.text))
					self.cursor_blit_position = self.font_object.get_rect(self.prompt + self.text[:self.cursor_position]).width

				elif event.key == pl.K_LEFT:
					# Subtract one from cursor_pos, but do not go below zero:
					self.cursor_position = max(self.cursor_position - 1, 0)
					self.cursor_blit_position = self.font_object.get_rect(self.prompt + self.text[:self.cursor_position]).width


				elif event.key == pl.K_END:
					self.cursor_position = len(self.text)
					self.cursor_blit_position = self.font_object.get_rect(self.prompt + self.text[:self.cursor_position]).width

				elif event.key == pl.K_HOME:
					self.cursor_position = 0
					self.cursor_blit_position = self.font_object.get_rect(self.prompt + self.text[:self.cursor_position]).width

				# Scroll the buffer - to the history
				elif event.key == pl.K_UP:
					# Only scroll if there is something in the buffer
					if len(self.buffer) > 0:
						# Calc new buffer position
						if self.buffer_offset >= 1: self.buffer_offset = self.buffer_offset - 1
						if len(self.buffer) == self.buffer_offset: self.buffer_offset = self.buffer_offset + 1 # fix
						#print(f"{self.buffer_offset=}, {len(self.buffer)=}")
						# Restore previous input string - last in buffer
						self.text = self.buffer[self.buffer_offset]						
						# Set cursor possition at the end of the string
						self.cursor_position = len(self.text)
						self.cursor_blit_position = self.font_object.get_rect(self.prompt + self.text[:self.cursor_position]).width

						# Regenerate text surfaces
						self.prepare_surface()

				# Scroll the buffer - to the future
				elif event.key == pl.K_DOWN:
					# Calc new buffer position
					if self.buffer_offset < len(self.buffer) - 1:
						self.buffer_offset = self.buffer_offset + 1
						# Restore previous input string - last in buffer
						self.text = self.buffer[self.buffer_offset]
						# Set cursor possition at the end of the string
						self.cursor_position = len(self.text)
						self.cursor_blit_position = self.font_object.get_rect(self.prompt + self.text[:self.cursor_position]).width

						# Regenerate text surfaces
						self.prepare_surface()

			elif event.type == pygame.TEXTINPUT:
				# Only add new characters if the max limit is not overreached
				#elif len(self.text) < self.max_input_text:					
				if len(self.text) < self.max_input_text:					
					# If no special key is pressed, add unicode of key to input_string
					self.text = (
						self.text[:self.cursor_position]
						#+ event.unicode
						+ event.text
						+ self.text[self.cursor_position:]
					)
					self.cursor_position += len(event.text)  # Some are empty, e.g. K_UP
					self.cursor_blit_position = self.font_object.get_rect(self.prompt + self.text[:self.cursor_position]).width

					# Regenerate text surfaces
					self.prepare_surface()

			elif event.type == pl.KEYUP:
				# *** Because KEYUP doesn't include event.unicode, this dict is stored in such a weird way
				if event.key in self.keyrepeat_counters:
					del self.keyrepeat_counters[event.key]

		#####
		# Update key pressed times
		#####
		# TODO - revise - Update key counters
		for key in self.keyrepeat_counters:

			self.keyrepeat_counters[key][0] += self.clock.get_time()  # Update clock			

			if self.keyrepeat_counters[key][0] >= self.repeat_keys_initial_ms:
				self.keyrepeat_counters[key][0] = (
					self.repeat_keys_initial_ms
					- self.repeat_keys_interval_ms
				)

				event_key, event_unicode = key, self.keyrepeat_counters[key][1]
				pygame.event.post(pygame.event.Event(pl.KEYDOWN, key=event_key, unicode=event_unicode))


		#####
		# Update cursor blink - TODO - revise - use console clock
		#####
		self.cursor_ms_counter += self.clock.get_time()
		if self.cursor_ms_counter >= self.cursor_switch_ms:
			self.cursor_ms_counter %= self.cursor_switch_ms
			self.cursor_visible = not self.cursor_visible
				
		# TODO - revise - use console clock - clock must tick in order to see blinking cursor!
		self.clock.tick()
		
		# Only if enter is pressed then True is returned, else False - important for the Console instance
		return False

	def show(self, surf, pos=(0,0)):
		''' Blits main surface, text cut surface, text line and cursor to
		the given surface.
		'''

		# Background surface blit
		surf.blit(self.surf, (int(pos[0]), int(pos[1])))
		
		# Clear the main text input surf on which the actual text is blitted
		self.txt_surf.fill((0,0,0,0)) # Last 0 indicates alpha, i.e. full transparency

		# Input text background blit
		if self.font_bck_color:			
			self.txt_surf.blit(self.fnt_bck_surf,
					(int(self.fnt_txt_scroll_offset),
					int(self.line_spacing - ((self.line_spacing - self.fnt_bck_surf_dim.height) // 2) - self.fnt_bck_surf_dim.height)))

		# Input text blit
		self.txt_surf.blit(self.fnt_txt_surf,
						(int(self.fnt_txt_scroll_offset),
						int(self.line_spacing - ((self.line_spacing - self.fnt_txt_surf_dim.height) // 2) - self.fnt_txt_surf_dim.height)))

		# Cursor blit
		if self.cursor_visible:
			self.txt_surf.blit(self.cursor_surf, 
						(int(self.fnt_txt_scroll_offset + self.cursor_blit_position),
						int(self.line_spacing - ((self.line_spacing - self.cursor_surf_dim.height) // 2) - self.cursor_surf_dim.height)))

		# Cutted text blit
		surf.blit(self.txt_surf, 
				(int(pos[0] + self.padding.left),
				int(pos[1] + self.padding.up)))

	def get_height(self):
		''' Returns current height of the text input surface. 
		Called from Console instance in order to construct all elements 
		of console and display correctly 
		'''		
		return self.surf_dim.height

	def get_text(self):
		''' Method that reads the text and passs it to the console
		'''
		return self.text

	def clear_text(self):
		''' Called from console after enter is pressed to clear the text
		on input and related parameters. 
		'''
		self.text = ''
		self.cursor_position = 0		
		self.cursor_blit_position = self.font_object.get_rect(self.prompt + self.text[:self.cursor_position]).width
		self.prepare_surface()

class Console(pygame.Surface):
	''' Class implementing the game console. Console is compraised by other 
	objects header, footer, input and output objects. If component is present
	or not in the console is defined by the config file.
	'''

	# List of available layouts for the console. If error, INPUT_BOTTOM is used as default.
	LAYOUTS = ['INPUT_BOTTOM', 'INPUT_TOP']

	# List of available animations for the console. If error, TOP is used as default.
	ANIMATIONS = ['TOP', 'BOTTOM']


	def __init__(self, app, width, config={}):
		'''
		:param app: Reference to the instance that is govern (is accessible) by/from the console
		:param width: Required width of the console window. Height is determined by height of individual console parts.
		:param config: Dictionary storing all the configs necessary for correct display of console. See keys explanation below:
			
			global (mandatory section, see defaults below): Parameters that govern global console configuration.
				animation (optional, default None) : Determines if displaying of the console is animated or not. 
					Possible values are None (no animation - blit on position), ['TOP', 1500] ... animation type and number of ms for showing console. ['TOP'] ... default 100ms will be used
				layout (optional, default 'INPUT_BOTTOM') : Determines the layout of header, footer, input and output part.
				padding (optional, default (0,0,0,0)): Specifies padding around the console window and console items. The padding order is UP, DOWN, LEFT, RIGHT
				bck_color (optional, default (0,0,0)): Color of the console background as tuple with 3 values.  Eg. (255,255,255) for white.
				bck_image (optional, default None): Path to image displayed as the console background.
				bck_image_resize (optional, default True): True/False, if image should be adjusted to the console dimensions.
				bck_alpha (optional, default 255): 0-255, Transparency of console background.
				welcome_msg (optional, default ''): Text displayed on console after console init.
				welcome_msg_color (optional, default (255,255,255)): Color of the console welcome text as tuple with 3 values.
				cmd_pckg_path (optional, default None): Package, where module with console commands can be found.
				script_path (optional, default None): Path, where console scripts can be found.
				
			header (optional section, see Header class for details): Parameters that govern console header configuration.
			output (optional section, see TextOutput class for details): Parameters that govern console output configuration.
			input (optional section, see TextInput class for details): Parameters that govern console input configuration.
			footer (optional section, see Header class for details): Parameters that govern console footer configuration.
		'''

		self.init(app=app, width=width, config=config)

		# Put the initial text on the console in given color - only for the first instantiation
		if self.console_output: self.write(self.welcome_msg, self.welcome_msg_color)

		# By default console is disabled
		self.enabled = False

	def init(self, width: int, config: dict={}, app=None):
		''' Can be called when the configuration is changed.

		:param app: Reference to the instance that is govern (is accessible) by/from the console
		:param width: Required width of the console window. Height is determined by height of individual console parts.
		:param config: Dictionary storing all the configs necessary for correct display of console. See keys explanation below:
			
			global (mandatory section, see defaults below): Parameters that govern global console configuration.
				animation (optional, default None) : Determines if displaying of the console is animated or not. 
					Possible values are None (no animation - blit on position), ['TOP', 1500] ... animation type and number of ms for showing console. ['TOP'] ... default 100ms will be used
				layout (optional, default 'INPUT_BOTTOM') : Determines the layout of header, footer, input and output part.
				padding (optional, default (0,0,0,0)): Specifies padding around the console window and console items. The padding order is UP, DOWN, LEFT, RIGHT
				bck_color (optional, default (0,0,0)): Color of the console background as tuple with 3 values.  Eg. (255,255,255) for white.
				bck_image (optional, default None): Path to image displayed as the console background.
				bck_image_resize (optional, default True): True/False, if image should be adjusted to the console dimensions.
				bck_alpha (optional, default 255): 0-255, Transparency of console background.
				welcome_msg (optional, default ''): Text displayed on console after console init.
				welcome_msg_color (otional, default (255,255,255)): Color of the console welcome text as tuple with 3 values.
				script_module_path: Where to look for the console scripts containing console commands.

			header (optional section, see Header class for details): Parameters that govern console header configuration.
			output (optional section, see TextOutput class for details): Parameters that govern console output configuration.
			input (optional section, see TextInput class for details): Parameters that govern console input configuration.
			footer (optional section, see Header class for details): Parameters that govern console footer configuration.
		'''

		self.app = app

		# Dictionary with default values
		default_config = {
						'animation' : None,
						'layout' : 'INPUT_BOTTOM',
						'padding' : (0,0,0,0),
						'bck_color' : (0,0,0),
						'bck_image' : None,
						'bck_image_resize' : True,
						'bck_alpha' : 128,
						'welcome_msg' : '',
						'welcome_msg_color' : (255,255,255)
					}

		# Merge default values with given values - overwrite defaults by config dict
		global_config = {**default_config, **config.get('global', {})}

		# Save the params from the config dict
		for key in global_config: setattr(self, key, global_config.get(key))

		# Instantiate padding for further use
		self.padding = Padding(self.padding)

		''' Initiates all console supporting objects - header, footer, 
		text_input and text_output.
		'''
		# Initiate header object, use defaults if header params are not passed during initiation
		self.console_header = Header(self, (width - self.padding.left - self.padding.right), config.get('header')) if config.get('header', None) else None

		# Initiate input text object - keep buffers on re-init
		try:
			buffer_bckp = self.console_input.buffer
			buffer_offset_bckp = self.console_input.buffer_offset
			self.console_input = TextInput(self, (width - self.padding.left - self.padding.right), config.get('input')) if config.get('input', None) else None
			self.console_input.buffer = buffer_bckp
			self.console_input.buffer_offset = buffer_offset_bckp
		except AttributeError: # console_input not yet initiated
			self.console_input = TextInput(self, (width - self.padding.left - self.padding.right), config.get('input')) if config.get('input', None) else None

		# Initiate output text object
		try:
			buffer_bckp = self.console_output.buffer
			buffer_offset_bckp = self.console_output.buffer_offset
			self.console_output = TextOutput(self, (width - self.padding.left - self.padding.right), config.get('output')) if config.get('output', None) else None
			self.console_output.buffer = buffer_bckp
			self.console_output.buffer_offset = buffer_offset_bckp
		except AttributeError: # console_input not yet initiated
			self.console_output = TextOutput(self, (width - self.padding.left - self.padding.right), config.get('output')) if config.get('output', None) else None

		# Initiate footer object
		self.console_footer = Header(self, width - self.padding.left - self.padding.right, config.get('footer')) if config.get('footer', None) else None		

		# Initiace object for processing console commands - output of the class is redirected
		# if console_output is not defined then standard output is used (sustem text console)
		self.cli = CommandLineProcessor(self.app, output=self.console_output, cmd_pckg_path=config.get('global').get('cmd_pckg_path', None), script_path=config.get('global').get('script_path', None)) if self.console_output else CommandLineProcessor(self.app)

		# Correct the height dimension so that all the text rows are displayable
		self.dim = (width, self.padding.up 
							+ (self.console_header.get_height() if self.console_header else 0)
							+ (self.console_output.get_max_height() if self.console_output else 0)
							+ (self.console_input.get_height() if self.console_input else 0)
							+ (self.console_footer.get_height() if self.console_footer else 0)
							+ self.padding.down)
		
		# Call the pygame.Surface initializer
		super().__init__(self.dim) 

		# If layout is not specified, use INPUT_BOTTOM layout as default
		self.layout = ('INPUT_BOTTOM' if self.layout not in Console.LAYOUTS else self.layout)

		# Prepare console background image
		if self.bck_image:
			self.bck_image = pygame.image.load(str(self.bck_image)).convert()
			if self.bck_image_resize:
				self.bck_image = pygame.transform.scale(self.bck_image, (self.dim))

		# Set Console transparency
		self.set_alpha(self.bck_alpha)

		''' Animation part - Prepare variables managing animation, if animation is enabled 
		'''
		if self.animation:
			# If specified animation layout is not found, 'TOP' layout will be used as default
			self.anim_layout = self.animation[0] if len(self.animation) > 0 and self.animation[0] in Console.ANIMATIONS else 'TOP'
			# If animation time is not specified use 100 ms
			self.anim_time = self.animation[1] if len(self.animation) > 1 else 100
			# Calculate animation velocity based on the console dimensions (height)
			self.anim_velocity = self.dim[1] / self.anim_time
			# Initiate variable for remembering the time
			self.anim_last_time = 0
			# Initiate variable for storing percentage of shown console surface (0 nothing shown, 100 all shown)
			self.anim_perc = 0

	def set_cli_app(self, module: str):
		'''Sets the module/class/function to be used as reference entry point to the game.
		'''
		try:
			import sys
			self.app=sys.modules[module] # must be called after the cli module is imported
			self.cli.app = self.app
		except KeyError:
			raise ValueError(f"{module} not yet imported. No console CLI module loaded.")


		# Get and translate the package-method pairs from text_params parameter
		try:
			tmp_text_params = []
			for pack_method in self.console_header.text_params: # iterate list of pack-method values
				package, method = pack_method
				package = self.app if package is None else package # if package is not specified use the console CLI app
				tmp_text_params.append([package, method])
			self.console_header.text_params = tmp_text_params
		except AttributeError:
			# if self.text_params are not defined, continue
			pass

		# Get and translate the package-method pairs from text_params parameter
		try:
			tmp_text_params = []
			for pack_method in self.console_footer.text_params: # iterate list of pack-method values
				package, method = pack_method
				package = self.app if package is None else package # if package is not specified use the console CLI app
				tmp_text_params.append([package, method])
			self.console_footer.text_params = tmp_text_params
		except AttributeError:
			# if self.text_params are not defined, continue
			pass

	def update(self, events):
		''' Call updates of relevant console parts. If ENTER was pressed, process the command.
		Only process if console is enabled.
		'''
		
		# Do update only if the console is active/enabled
		if self.enabled:

			# If console has defined input and enter is pressed (entering command into the console)
			if self.console_input and self.console_input.update(events):
				
				# Put it into the textoutput - if output is defined
				if self.console_output: self.console_output.write(self.console_input.get_text(), self.console_input.font_color)

				# Process the entered line by CLI instance
				self.cli.onecmd(self.console_input.get_text())
				
				# Reset the text, so that new one can be entered
				self.console_input.clear_text()

			# Check if text output keys for scrolling the buffer were used
			if self.console_output: self.console_output.update(events)

			# Update the header - in order to update the dynamic values shown in the header
			if self.console_header: self.console_header.update()

			# Update the footer - in order to update the dynamic values shown in the footer
			if self.console_footer: self.console_footer.update()

	def show(self, surf, pos=None, disable_anim=None):
		''' Manages bliting of console (background, textoutput, textinput)
		to the given surf surface and on given pos position. Also manages displaying
		of proper animation, if enabled by configuration.

		If animation is enabled, possition of blitting of every part must be adjusted 
		so that we reach required animation effect. The pos parameter is marking the final
		origin where the fully displayed console is placed.

		If parameter disable_anim is set to True, animation is forcefully disabled.
		'''

		#####
		# Calculate the delta parameters for displaying animated console
		#####		

		# No animation required - no delta from original position. Console is either fully shown or fully hidden.
		if not self.animation or disable_anim:
			
			# In no position is entered go for upper left corner
			pos = (0,0) if not pos else pos

			anim_dx = 0		
			anim_dy = 0

			if self.enabled: self.anim_perc = 100
			else: self.anim_perc = 0

		# Animation required - based on animation parameters calculate the portion of the console to be displayed
		# expressed by delta parameters anim_dx and anim_dy.
		else:
	
			current_time = pygame.time.get_ticks()

			#####
			# Update percentage of animation shown and the time
			#####

			# If console is enabled, I need to continue animation or show full console if animation is finished or no animation is requested.
			# If console is disabled, I need to continue hiding animation or fully hide the console if animation is finished
			if (self.enabled and self.anim_perc < 100) or (not self.enabled and self.anim_perc > 0):
				self.anim_perc = self.anim_perc + (1 if self.enabled else -1) * (current_time - self.anim_last_time) * self.anim_velocity 
				self.anim_last_time = current_time 

			# Do correction in case that console is fully displayed or fully hidden
			self.anim_perc = 100 if self.anim_perc > 100 else self.anim_perc
			self.anim_perc = 0 if self.anim_perc < 0 else self.anim_perc

			#####
			# Prepare the coordinates for animation based on animation layout
			#####

			# Pos parameter that is passed to show function should refer to the top edge of the surface
			if self.anim_layout == 'TOP':
				# For the best results TOP animation should happen from the upper edge of the screen  (surface)
				pos = (0,0) if not pos else pos
				# Movement is only on Y axis, hence no need to adjust X axis
				anim_dx = 0
				# Correction of Y coordinate base on percentage of console that we need to display
				anim_dy =  -self.dim[1] * (1 - self.anim_perc / 100)

			# Pos parameter that is passed to the show function should refer to the bottom edge of the surface
			if self.anim_layout == 'BOTTOM':
				# For the best results TOP animation should happen from the bottom edge of the screen (surface)
				pos = (0,surf.get_height()) if not pos else pos
				# Movement is only on Y axis, hence no need to adjust X axis
				anim_dx = 0
				# Correction of Y coordinate base on percentage of console that we need to display
				anim_dy =  -self.dim[1] * (1 - (100 - self.anim_perc) / 100)


		#####
		# Display the console to the surface, if needed - anim_perc > 0
		#####		

		# This happens when console is either enabled or disabled and is being hidden
		if self.anim_perc > 0:

			#####
			# Prepare the individual console components coordinates based on the layout. More layouts can be added here.
			#####

			# Calculate position of layout items on the console based on the layout	must be done here as the console output height is changing
			# based on lines displayed on the output.
			if self.layout == 'INPUT_BOTTOM':
				self.header_position = (self.padding.left, self.padding.up)
				self.text_output_position = (self.padding.left, self.header_position[1] + (self.console_header.get_height() if self.console_header else 0))
				self.text_input_position = (self.padding.left, self.text_output_position[1] + (self.console_output.get_height() if self.console_output else 0))
				self.footer_position = (self.padding.left, self.dim[1] - self.padding.down - (self.console_footer.get_height() if self.console_footer else 0))		

			if self.layout == 'INPUT_TOP':
				self.header_position = (self.padding.left, self.padding.up)
				self.text_input_position = (self.padding.left, self.header_position[1] + (self.console_header.get_height() if self.console_header else 0))
				self.text_output_position = (self.padding.left, self.text_input_position[1] + (self.console_input.get_height() if self.console_input else 0))
				self.footer_position = (self.padding.left, self.dim[1] - self.padding.down - (self.console_footer.get_height() if self.console_footer else 0))		

			#####
			# Blit everything with the corrections
			#####

			# Clear Console background surface		
			self.fill(self.bck_color)

			# If background image is defined, paste it to console surface
			if self.bck_image: self.blit(self.bck_image, (0, 0))

			# Blit console background to the surface
			surf.blit(self, (int(pos[0] + anim_dx), int(pos[1] + anim_dy)))

			# Blit header onto the surface - by calling show and not blitting directly enables
			# transparent background and non transparent text displayed on it.
			if self.console_header:
				self.console_header.show(
					surf,
					(int(pos[0] + anim_dx + self.header_position[0]),
					int(pos[1] + anim_dy + self.header_position[1]))
					)

			# Blit output onto the surface
			# Based on parameter text_input_position either on top or at the bottom of the console
			if self.console_output:
				self.console_output.show(
					surf,
					(int(pos[0] + anim_dx + self.text_output_position[0]),
					int(pos[1] + anim_dy + self.text_output_position[1]))
					)
			
			# Blit input surface onto the surface
			# Based on parameter text_input_position either on top or at the bottom of the console
			if self.console_input:
				self.console_input.show(
					surf,
					(int(pos[0] + anim_dx + self.text_input_position[0]),
					int(pos[1] + anim_dy + self.text_input_position[1]))
					)		

			# Blit footer onto the surface
			if self.console_footer:
				self.console_footer.show(
					surf,
					(int(pos[0] + anim_dx + self.footer_position[0]),
					int(pos[1] + anim_dy + self.footer_position[1]))
					)
	
	def write(self, text, color=None):
		''' Put some text onto a console by calling this function
		'''
		self.console_output.write(str(text), color)

		# Without calling prepare_surface the text will not be shown immediatelly
		self.console_output.prepare_surface()

	def toggle(self, enable=None) -> bool:
		''' Toggle on/off the console. Influences if updade and show console functions are 
		working.

		If enable parameter is True, showing of console is forced.
		If enable parameter is False, hidding of the console is forced.
		'''
		# Toggle on/off the console
		self.enabled = not self.enabled if enable is None else enable

		# Remember toggle time for smooth animation purposes
		if self.animation: self.anim_last_time = pygame.time.get_ticks()

		# Delete the memory of keyrepeats - otherwise it might happen that keys are automatically pressed after toggle
		self.console_input.keyrepeat_counters.clear()

		# Return the new state
		return self.enabled

	def reset(self):
		''' Method that reloads and resets the console
		'''
		pass

	def clear(self):
		''' Method that clears the output on the screen
		'''
		self.console_output.log = list()
		self.console_output.prepare_surface()
