import numpy as np 
import random
import math
import time 

# =======================================================================
#               MOCK C++ CORE DEFINITIONS & CONSTANTS 
# =======================================================================

# --- Movement/Physics ---
MOVE_SPEED = 10.0
SPRINT_MULTIPLIER = 2.5 # Player can sprint 2.5 times faster
JUMP_VELOCITY = 15.0

# --- Weapon & AI ---
BOT_CHASE_SPEED = 8.0 
WEAPON_MASTER_LIST = {
    '01_PLASMA_RIFLE': {'damage': 55.0, 'rpm': 450, 'spread': 0.00, 'mode': 'AUTO', 'projectiles': 1},
    '02_OMEGA_SHOTGUN': {'damage': 15.0, 'rpm': 90, 'spread': 1.5, 'mode': 'SEMI', 'projectiles': 8},
    '03_RAIL_CANNON': {'damage': 300.0, 'rpm': 30, 'spread': 0.00, 'mode': 'SINGLE', 'projectiles': 1},
    # The remaining 37 weapons would be defined here
}

# 1. Mock AuraObject (Updated with Sprint Flag)
class AuraObject:
    """Mock class representing an object managed by the C++ core."""
    def __init__(self, name, mass, position, linear_velocity, is_static, health, is_bot=False):
        self.name = name
        self.mass = mass
        self.position = position
        self.linear_velocity = linear_velocity
        self.is_static = is_static
        self.health = health
        self.render_comp = type('RenderComp', (object,), {'is_visible': True})()
        self.on_ground = True 
        self.is_bot = is_bot
        self.state = 'IDLE' if is_bot else 'PLAYER'
        self.is_sprinting = False # NEW: Flag for sprinting state
        self.orientation = type('Orientation', (object,), {
            'as_matrix': lambda self_ignored: np.eye(3) 
        })()
        
    def shoot(self, target):
        print(f"[{self.name}] Firing conceptual projectile at {target.name}!")

# 2. Mock OCPE_GameEngine (Unchanged for this step)
class OCPE_GameEngine_Mock:
    def __init__(self):
        print("\n[OCPE Mock] Initializing Mock C++ Core.")
        self.actors = [] 
        # ... (run_physics_step and shoot_raycast methods omitted for brevity) ...
    def run_physics_step(self, dt):
        for actor in self.actors:
            if not actor.is_static:
                # Apply sprinting multiplier if active
                move_mult = SPRINT_MULTIPLIER if actor.is_sprinting else 1.0
                actor.linear_velocity[1] -= 9.8 * dt
                actor.position += actor.linear_velocity * dt * move_mult
    def shoot_raycast(self, start_pos, direction_vector, damage):
        print(f"  -> C++ Core Mock: Raycasting from {start_pos.astype(int)}...")
        return None

# =======================================================================
#                  NEW: MAP AND LOOT MANAGER
# =======================================================================

class LootChest:
    """Represents a weapon chest object on the map."""
    def __init__(self, position, weapon_id):
        self.position = np.array(position).astype(float)
        self.weapon_id = weapon_id
        self.is_open = False
        self.interaction_range = 3.0
        
    def interact(self, player_position, weapon_manager):
        """Checks distance and gives the player the weapon."""
        distance = np.linalg.norm(player_position - self.position)
        
        if distance <= self.interaction_range and not self.is_open:
            weapon_manager.switch_weapon(self.weapon_id)
            self.is_open = True
            print(f"  -> Chest opened! Player received: **{self.weapon_id}**")
            return True
        elif self.is_open:
            print("  -> Chest is already empty.")
        else:
            print(f"  -> Too far to interact. Distance: {distance:.2f}m")
        return False

class MapManager:
    """Defines the conceptual layout of the large map."""
    def __init__(self, engine_mock):
        self.engine = engine_mock
        self.loot_chests = []
        
        # Conceptual Map Geometry and Zones
        self.ZONES = {
            'A1_DOWNTOWN': {'center': (100, 100), 'size': 50},
            'B3_BUNKER': {'center': (500, 500), 'size': 20, 'is_hiding': True},
            'C5_CAVE': {'center': (800, 200), 'size': 30, 'is_hiding': True},
        }
        
        self.setup_map()

    def setup_map(self):
        """Spawns key map objects like chests and obstacles."""
        print("\n[Map Manager] Building Large Map Geometry (1000x1000 units)...")
        
        # Spawn the first Loot Chest near the Bunker
        chest1 = LootChest(
            position=np.array([505.0, 1.0, 505.0]), # Near B3_BUNKER
            weapon_id='02_OMEGA_SHOTGUN' 
        )
        self.loot_chests.append(chest1)
        print(f"  -> Spawned Loot Chest ({chest1.weapon_id}) at {chest1.position.astype(int)}")

        # Spawn a second chest in the center of the Cave
        chest2 = LootChest(
            position=np.array([800.0, 5.0, 200.0]),
            weapon_id='03_RAIL_CANNON'
        )
        self.loot_chests.append(chest2)
        print(f"  -> Spawned Loot Chest ({chest2.weapon_id}) at {chest2.position.astype(int)}")
        
        # Conceptual large structures for hiding
        for name, data in self.ZONES.items():
            if data.get('is_hiding'):
                print(f"  -> Placed large **Hiding Structure** (Zone: {name}) at {data['center']}")

# =======================================================================
#                  INPUT MANAGER (Updated with Controls)
# =======================================================================

class InputManager:
    """Handles conceptual input."""
    def __init__(self, engine_mock, weapon_manager, map_manager):
        self.joystick_state = {'X': 0.0, 'Y': 0.0} # X for strafe, Y for forward/back
        self.action_buttons = {'jump': False, 'shoot': False, 'build': False, 'interact': False, 'sprint': False}
        self.engine = engine_mock
        self.weapon_manager = weapon_manager 
        self.map_manager = map_manager # NEW: Reference to the map manager
        
    def process_movement(self, player):
        """Calculates player velocity based on joystick and sprint state."""
        
        # Update player sprint state
        player.is_sprinting = self.action_buttons['sprint']
        
        # Calculate velocity vector
        player.linear_velocity[0] = self.joystick_state['X'] * MOVE_SPEED
        player.linear_velocity[2] = self.joystick_state['Y'] * MOVE_SPEED
        
    def process_actions(self, player, build_manager):
        
        if self.action_buttons['interact']:
            # --- Map Interaction Logic ---
            print(f"\n[Input] Player tries to Interact at {player.position.astype(int)}...")
            for chest in self.map_manager.loot_chests:
                if chest.interact(player.position, self.weapon_manager):
                    break # Stop after interacting with one chest
            self.action_buttons['interact'] = False
                
        # ... (shoot and build logic omitted for brevity) ...

    def on_key_press(self, key_code):
        if key_code == 'W':
            self.joystick_state['Y'] = 1.0 # Forward
        elif key_code == 'A':
            self.joystick_state['X'] = -1.0 # Strafe Left
        elif key_code == 'D':
            self.joystick_state['X'] = 1.0 # Strafe Right
        elif key_code == 'LSHIFT':
            self.action_buttons['sprint'] = True # NEW: Start Sprinting
        elif key_code == 'E':
            self.action_buttons['interact'] = True # NEW: Interact
        # ... (LMB, 1, 2, 3 logic omitted for brevity) ...

    def on_key_release(self, key_code):
        if key_code == 'W' or key_code == 'S':
            self.joystick_state['Y'] = 0.0
        elif key_code == 'A' or key_code == 'D':
            self.joystick_state['X'] = 0.0
        elif key_code == 'LSHIFT':
            self.action_buttons['sprint'] = False # NEW: Stop Sprinting

# ... (WeaponManager, Renderer, BotAIController classes omitted for brevity) ...

class WeaponManager:
    def __init__(self, engine_mock, master_list):
        self.engine = engine_mock
        self.master_list = master_list
        self.active_weapon_id = '01_PLASMA_RIFLE'
        self.last_fire_time = 0.0
    def switch_weapon(self, new_id):
        self.active_weapon_id = new_id
        print(f"  -> Switched to **{new_id}**.")
    def try_fire(self, player_pos, player_direction): pass

# =======================================================================
#                             TEST EXECUTION (Map and Movement Focus)
# =======================================================================

# 1. Initialize Core Systems
ocpe_mock = OCPE_GameEngine_Mock()
map_manager = MapManager(ocpe_mock)
weapon_manager = WeaponManager(ocpe_mock, WEAPON_MASTER_LIST)
input_manager = InputManager(ocpe_mock, weapon_manager, map_manager) 

# 2. Create Actors
player = AuraObject(
    name="MasterPlayer", 
    mass=75, 
    # Start near the first chest (at 500, 10, 500)
    position=np.array([495.0, 1.0, 500.0]), 
    linear_velocity=np.array([0.0, 0.0, 0.0]), 
    is_static=False, 
    health=100.0
)
ocpe_mock.actors.append(player)

print(f"\n--- STARTING OMEGA-COREBOT MAP TEST ---")
print(f"Initial Weapon: {weapon_manager.active_weapon_id}")

# Simulate a series of actions
for frame in range(1, 10):
    dt = 1.0 # Use a large dt for visible position changes in the mock
    print(f"\n--- FRAME {frame} (DT: {dt}s) ---")
    
    if frame == 1:
        # Player starts walking forward towards the chest at [505, 505]
        input_manager.on_key_press('W')
        
    if frame == 2:
        # Player starts sprinting! (Should move 2.5x faster)
        input_manager.on_key_press('LSHIFT') 
        
    if frame == 4:
        # Player is close enough, stop and interact
        input_manager.on_key_release('W')
        input_manager.on_key_release('LSHIFT')
        input_manager.on_key_press('E')

    # --- Execute Game Loop ---
    input_manager.process_movement(player)
    input_manager.process_actions(player, None) 
    ocpe_mock.run_physics_step(dt) 

    current_speed = np.linalg.norm(player.linear_velocity)
    print(f"Player Position: {player.position.astype(int)} | Speed: {current_speed:.1f} m/s | Sprinting: {player.is_sprinting}")

print("\n--- MAP AND LOOT SYSTEM TEST COMPLETE ---")
print(f"Final Weapon: {weapon_manager.active_weapon_id}")
