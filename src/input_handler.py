import pygame

class InputHandler:
    def __init__(self):
        self.key_bindings = {
            'move_right': pygame.K_RIGHT,
            'move_left': pygame.K_LEFT,
            'move_up': pygame.K_UP,
            'move_down': pygame.K_DOWN,
            'fire': pygame.K_SPACE,
            'quit': pygame.K_q,
            'pause': pygame.K_ESCAPE
        }
        
        # Reverse mapping for easy lookup
        self.action_map = {value: key for key, value in self.key_bindings.items()}
        
        # Track pressed keys
        self.pressed_keys = set()
        
    def update(self):
        """Update the state of pressed keys."""
        keys = pygame.key.get_pressed()
        self.pressed_keys.clear()
        for key_code, pressed in enumerate(keys):
            if pressed:
                self.pressed_keys.add(key_code)
    
    def is_action_pressed(self, action):
        """Check if an action's key is currently pressed."""
        if action in self.key_bindings:
            return self.key_bindings[action] in self.pressed_keys
        return False
    
    def get_key_name(self, key_code):
        """Get a human-readable name for a key code."""
        try:
            name = pygame.key.name(key_code).upper()
            # Special cases for better display
            if name == 'RETURN':
                return 'RETURN'
            elif name == 'RIGHT':
                return 'RIGHT'
            elif name == 'LEFT':
                return 'LEFT'
            elif name == 'UP':
                return 'UP'
            elif name == 'DOWN':
                return 'DOWN'
            elif name == 'SPACE':
                return 'SPACE'
            return name
        except:
            return f"KEY_{key_code}"
    
    def set_key_binding(self, action, key):
        """Set a new key binding for an action."""
        if action in self.key_bindings:
            # Don't allow ESC key to be bound
            if key == pygame.K_ESCAPE:
                print("Cannot bind ESC key")
                return False
                
            # If key is already bound to another action, swap the bindings
            if key in self.action_map and self.action_map[key] != action:
                other_action = self.action_map[key]
                old_key = self.key_bindings[action]
                
                # Update both bindings
                self.key_bindings[other_action] = old_key
                self.key_bindings[action] = key
                
                # Update action map
                self.action_map[old_key] = other_action
                self.action_map[key] = action
                
                print(f"Swapped bindings: {action} -> {self.get_key_name(key)}, {other_action} -> {self.get_key_name(old_key)}")
                return True
            else:
                # Remove old mapping from action_map
                old_key = self.key_bindings[action]
                if old_key in self.action_map:
                    del self.action_map[old_key]
                
                # Update key bindings
                self.key_bindings[action] = key
                self.action_map[key] = action
                
                print(f"Set {action} to key {self.get_key_name(key)} (code: {key})")
                return True
        return False
    
    def get_action_for_key(self, key):
        """Get the action bound to a key."""
        return self.action_map.get(key)
    
    def is_key_bound(self, key):
        """Check if a key is already bound to an action."""
        return key in self.action_map
    
    def get_current_binding(self, action):
        """Get the current key bound to an action."""
        return self.key_bindings.get(action) 
    
    def is_key_for_action(self, key, action):
        """Check if a key is bound to a specific action."""
        return self.key_bindings.get(action) == key 