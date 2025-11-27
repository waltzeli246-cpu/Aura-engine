import numpy as np 
import random
import math
import time # Needed for Rate of Fire (RoF) tracking

# =======================================================================
#               MOCK C++ CORE DEFINITIONS & CONSTANTS 
# =======================================================================

MOVE_SPEED = 10.0
JUMP_VELOCITY = 15.0
BOT_CHASE_SPEED = 8.0 
BOT_VISION_RANGE_SQ = 2500.0 
BOT_ATTACK_RANGE_SQ = 400.0 
WEAPON_DAMAGE = 34.0
# --- NEW: Weapon Master List (The first few of 40) ---
WEAPON_MASTER_LIST = {
    '01_PLASMA_RIFLE': {'damage': 55.0, 'rpm': 450, 'spread': 0.00, 'mode': 'AUTO', 'projectiles': 1},
    '02_OMEGA_SHOTGUN': {'damage': 15.0, 'rpm': 90, 'spread': 1.5, 'mode': 'SEMI', 'projectiles': 8},
    '03_RAIL_CANNON': {'damage': 300.0, 'rpm': 30, 'spread': 0.00, 'mode': 'SINGLE', 'projectiles': 1},
    '04_EMP_GRENADE': {'damage': 0.0, 'rpm': 10, 'spread': 0.00, 'mode': 'SINGLE', 'projectiles': 1},
    # ... (36 more conceptual weapons would go here)
}

# 1. Mock AuraObject (Unchanged)
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
        self.orientation = type('Orientation', (object,), {
            'as_matrix': lambda self_ignored: np.eye(3) 
        })()
        
    def shoot(self, target):
        print(f"[{self.name}] Firing conceptual projectile at {target.name}!")

# 2. Mock OCPE_GameEngine (Unchanged)
class OCPE_GameEngine_Mock:
    """Mocks the C++ engine to prevent errors in Python logic."""
    # ... (methods from previous step)
    def __init__(self):
        print("\n[OCPE Mock] Initializing Mock C++ Core. GPU Dynamics NOT Enabled.")
        self.actors = [] 

    def run_physics_step(self, dt):
        for actor in self.actors:
            if not actor.is_static:
                actor.linear_velocity[1] -= 9.8 * dt
                actor.position += actor.linear_velocity * dt

    def shoot_raycast(self, start_pos, direction_vector, damage):
        """Mocks the C++ ShootAndDamage PhysX call."""
        print(f"  -> C++ Core Mock: Raycasting from {start_pos.astype(int)}...")
        
        for actor in self.actors:
            if actor.name.startswith("OMEGA-BOT") and actor.health > 0:
                distance_sq = np.sum((actor.position - start_pos)**2)
                # Simple mock: 70% chance to hit a bot within 50 units
                if distance_sq < 2500.0 and random.random() < 0.7: 
                    actor.health -= damage
                    print(f"  -> HIT! {actor.name} took {damage:.1f} damage. Health: {actor.health:.1f}")
                    return actor 
                    
        print("  -> MISS. No target hit.")
        return None

# =======================================================================
#                  NEW: AURA WEAPON MANAGER
# =======================================================================

class WeaponManager:
    """Manages all 40 weapons, fire rate, and logic."""
    def __init__(self, engine_mock, master_list):
        self.engine = engine_mock
        self.master_list = master_list
        self.active_weapon_id = '01_PLASMA_RIFLE'
        self.last_fire_time = 0.0

    def switch_weapon(self, new_id):
        """Changes the player's active weapon."""
        if new_id in self.master_list:
            self.active_weapon_id = new_id
            print(f"[Weapon Manager] Switched to **{new_id}**.")
        else:
            print(f"[Weapon Manager] ERROR: Weapon ID {new_id} not found.")

    def try_fire(self, player_pos, player_direction):
        """Calculates RoF, spread, and calls the C++ raycast."""
        weapon_data = self.master_list[self.active_weapon_id]
        current_time = time.time()
        
        # 1. Rate of Fire Check
        fire_delay = 60.0 / weapon_data['rpm'] # Convert RPM to seconds
        if current_time - self.last_fire_time < fire_delay:
            return # Cannot fire yet

        self.last_fire_time = current_time
        
        print(f"[Weapon Manager] Firing {self.active_weapon_id}...")
        
        # 2. Projectile Loop (for shotguns, etc.)
        for i in range(weapon_data['projectiles']):
            
            # 3. Apply Conceptual Spread (Random offset to the direction vector)
            spread_angle = weapon_data['spread']
            
            # Small random vector perpendicular to the main direction
            if spread_angle > 0:
                offset_x = random.uniform(-spread_angle, spread_angle)
                offset_y = random.uniform(-spread_angle, spread_angle)
                
                # Apply the offset (conceptual calculation)
                final_direction = player_direction + np.array([offset_x, offset_y, 0]) 
                final_direction /= np.linalg.norm(final_direction) # Re-normalize
            else:
                final_direction = player_direction
            
            # 4. Call the C++ Core Raycast!
            self.engine.shoot_raycast(
                player_pos, 
                final_direction, 
                weapon_data['damage']
            )

# =======================================================================
#                  INPUT MANAGER (Updated to use WeaponManager)
# =======================================================================

class InputManager:
    """Handles conceptual input."""
    def __init__(self, engine_mock, weapon_manager):
        self.joystick_state = {'X': 0.0, 'Y': 0.0} 
        self.action_buttons = {'jump': False, 'shoot': False, 'build': False}
        self.engine = engine_mock
        self.weapon_manager = weapon_manager # NEW: Reference to the manager
        
    # ... (other methods removed for brevity) ...

    def process_actions(self, player, build_manager):
        # ... (jump and build logic) ...
                
        if self.action_buttons['shoot']:
            # Direction is simplified to straight ahead for this mock
            player_direction = np.array([0.0, 0.0, -1.0]) 
            
            # --- Weapon System INTEGRATION ---
            self.weapon_manager.try_fire(player.position, player_direction)
            
            # Don't reset the shoot button for 'AUTO' mode in this simple mock
            if self.weapon_manager.master_list[self.weapon_manager.active_weapon_id]['mode'] != 'AUTO':
                 self.action_buttons['shoot'] = False 

    def on_key_press(self, key_code):
        # ... (W and Space logic) ...
        if key_code == 'LMB': 
            self.action_buttons['shoot'] = True
        
        # --- NEW: Weapon Switching Logic ---
        if key_code == '1':
            self.weapon_manager.switch_weapon('01_PLASMA_RIFLE')
        elif key_code == '2':
            self.weapon_manager.switch_weapon('02_OMEGA_SHOTGUN')
        elif key_code == '3':
            self.weapon_manager.switch_weapon('03_RAIL_CANNON')

    def on_key_release(self, key_code):
        # ... (W and Space logic) ...
        if key_code == 'LMB': 
            self.action_buttons['shoot'] = False # For AUTO/SEMI mode release

# ... (other classes (Renderer, BotAIController, etc.) are omitted for brevity but remain from the previous, correct step) ...

# =======================================================================
#                             TEST EXECUTION (Weapon Focus)
# =======================================================================

# 1. Initialize Core Systems
ocpe_mock = OCPE_GameEngine_Mock()
# Initialize Weapon Manager
weapon_manager = WeaponManager(ocpe_mock, WEAPON_MASTER_LIST)
# Pass the manager to the InputManager
input_manager = InputManager(ocpe_mock, weapon_manager) 

# Create Actors (Player and a Bot)
player = AuraObject(
    name="MasterPlayer", 
    mass=75, 
    position=np.array([0.0, 10.0, 0.0]), 
    linear_velocity=np.array([0.0, 0.0, 0.0]), 
    is_static=False, 
    health=100.0
)
bot = AuraObject(
    name="OMEGA-BOT-9000",
    mass=90,
    position=np.array([0.0, 10.0, -5.0]), # Bot is close and directly in front
    linear_velocity=np.array([0.0, 0.0, 0.0]),
    is_static=False,
    health=100.0,
    is_bot=True
)

ocpe_mock.actors.extend([player, bot])

print("\n--- STARTING OMEGA-COREBOT WEAPON MANAGER TEST ---")
print(f"Bot Health: {bot.health:.1f}")

# Simulate a series of actions
for frame in range(1, 10):
    dt = 1.0 / 60.0 
    print(f"\n--- FRAME {frame} ---")

    if frame == 1:
        input_manager.on_key_press('1') # Start with Plasma Rifle (AUTO)
        input_manager.on_key_press('LMB') # Start holding down fire
        
    if frame == 4:
        input_manager.on_key_release('LMB') # Stop firing Plasma Rifle
        input_manager.on_key_press('2') # Switch to Shotgun
        
    if frame == 5:
        input_manager.on_key_press('LMB') # Fire Shotgun (SEMI)
        
    if frame == 6:
        input_manager.on_key_release('LMB') 
        input_manager.on_key_press('3') # Switch to Rail Cannon
        
    if frame == 7:
        input_manager.on_key_press('LMB') # Fire Rail Cannon (SINGLE)
        
    # --- Execute Game Loop ---
    input_manager.process_actions(player, None) # Checks for shoot
    ocpe_mock.run_physics_step(dt) 

    
print("\n--- WEAPON MANAGER TEST COMPLETE ---")
print(f"Final Bot Health: {bot.health:.1f}")
