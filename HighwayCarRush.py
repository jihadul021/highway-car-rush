from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random


WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
camera_angle = 0
camera_distance = 250
camera_height = 100
camera_view_mode = 0 

BRIDGEWIDTH = 220
BRIDGE_INTERVAL = 1200
BRIDGE_RAMP_LEN = 250.0
BRIDGE_DECK_HEIGHT = 45.0
LANE_WIDTH = 60
ROAD_HALF_WIDTH = 200

MAX_SPEED = 2.0
ACCELERATION = 0.04
FRICTION = 0.98
GRAVITY = 0.5

# Traffic zebra
TRAFFIC_LIGHT_CYCLE = 500
ZEBRA_INTERVAL = 500
FPS = 60
ZEBRA_ZONE_HALF_LEN = 45
PED_DESPAWN_FRAMES = 3 * FPS
GREEN_MIN = 10 * FPS
GREEN_MAX = 20 * FPS
RED_FRAMES = 5 * FPS
PED_Y = 8
PED_SPEED = 1.2
PED_RADIUS = 12

#grenade and magnet
GRENADE_SPEED = 5.0
GRENADE_LIFETIME = 60
MAGNET_DURATION = 300

game_over = False
score = 0
distance_travelled = 0
frame_counter = 0
cheat_mode = False
is_day = True
theme = "urban"

player_pos = [0, 0, 0]
player_vel_y = 0
player_speed = 0.0
player_rotation = 0.0
player_lane = 1
is_jumping = False
car_damage_level = 0
hood_angle = 0
wheel_rotation = 0

# Environment
bridges = []
ramps = []
road_segments = []
next_ramp_distance = 700
next_bridge_distance = 1000
next_zebra_distance = 500
earthquake_intensity = 0.0
earthquake_timer = 0
time_of_day_timer = 1000

# Entities
traffic_cars = []
point_objects = []
static_obstacles = []
moving_obstacles = []
grenades = []
zebra_crossings = []
pedestrians = []

spawn_timer = 0
ai_cooldown = 0
grenade_cooldown = 0
magnet_pos = []
magnet_active = False
magnet_timer = 0
auto_drive_mode = False
last_red_zebra_fined = None


#Helpers

def draw_cylinder(radius, height, slices=12):
    q = gluNewQuadric()
    gluCylinder(q, radius, radius, height, int(slices), 1)
    glPushMatrix()
    glScalef(-1, 1, 1)
    gluDisk(q, 0, radius, int(slices), 1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, height)
    gluDisk(q, 0, radius, int(slices), 1)
    glPopMatrix()

def draw_sphere(radius, slices=12, stacks=12):
    q = gluNewQuadric()
    gluSphere(q, radius, int(slices), int(stacks))

def draw_cone(base, height, slices=12):
    q = gluNewQuadric()
    gluCylinder(q, base, 0, height, int(slices), 1)
    glPushMatrix()
    glScalef(-1, 1, 1)
    gluDisk(q, 0, base, int(slices), 1)
    glPopMatrix()

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


#Road and env
def get_road_y(z):
    base_y = 0.0
    for (z_start, z_end) in bridges:
        start = max(z_start, z_end)
        end = min(z_start, z_end)
        if z <= start and z >= end:
            dist_from_start = start - z
            dist_from_end = z - end
            if dist_from_start < BRIDGE_RAMP_LEN:
                ratio = dist_from_start / BRIDGE_RAMP_LEN
                return base_y + BRIDGE_DECK_HEIGHT * ratio
            elif dist_from_end < BRIDGE_RAMP_LEN:
                ratio = dist_from_end / BRIDGE_RAMP_LEN
                return base_y + BRIDGE_DECK_HEIGHT * ratio
            else:
                return base_y + BRIDGE_DECK_HEIGHT
    return base_y

def spawn_bridge_if_needed():
    global next_bridge_distance, bridges
    if distance_travelled < next_bridge_distance:
        return
    z_start = player_pos[2] - 1200
    z_end = z_start - BRIDGE_RAMP_LEN * 2 - 400
    bridges.append((z_start, z_end))
    next_bridge_distance += 1000

def spawn_ramp_if_needed():
    global ramps, next_ramp_distance, distance_travelled
    if distance_travelled < next_ramp_distance: return
    spawn_z = player_pos[2] - 1500
    if len(ramps) < 2 and get_road_y(spawn_z) < 1.0: 
        lane = random.randint(0, 2)
        ramps.append([(lane - 1) * LANE_WIDTH, 0, spawn_z])
        next_ramp_distance = distance_travelled + random.randint(500, 900)
    else:
        next_ramp_distance = distance_travelled + 100

def spawn_entities():
    global traffic_cars, point_objects, static_obstacles, spawn_timer
    if spawn_timer > 0:
        spawn_timer -= 1
        return
    spawn_z = player_pos[2] - 1200
    
    if random.random() < 0.05:
        spawn_type = random.choice(['cars', 'obstacles', 'coins'])
        if spawn_type == 'cars':
            open_lane = random.randint(0, 2)
            for lane_idx in range(3):
                if lane_idx != open_lane:
                    if random.random() < 0.7:
                        lane_x = (lane_idx - 1) * LANE_WIDTH
                        speed = random.uniform(0.5, 0.8)
                        spawn_y = get_road_y(spawn_z)
                        traffic_cars.append([lane_x, spawn_y, spawn_z, speed, 2])
            spawn_timer = 60
        elif spawn_type == 'obstacles':
            open_lane = random.randint(0, 2)
            for lane_idx in range(3):
                if lane_idx != open_lane:
                    if random.random() < 0.6:
                        lane_x = (lane_idx - 1) * LANE_WIDTH
                        static_obstacles.append([lane_x, 10, spawn_z])
            spawn_timer = 50
        elif spawn_type == 'coins':
            lane = random.randint(0, 2)
            lane_x = (lane - 1) * LANE_WIDTH
            point_objects.append([lane_x, 10, spawn_z])
            spawn_timer = 10

def spawn_zebra_crossing_if_needed():
    global next_zebra_distance, zebra_crossings
    if distance_travelled < next_zebra_distance:
        return
    z_pos = player_pos[2] - 900
    zebra_crossings[:] = zebra_crossings[-3:]
    for existing in zebra_crossings:
        if abs(existing[0] - z_pos) < 300:
            next_zebra_distance += ZEBRA_INTERVAL
            return
    green_time = random.randint(GREEN_MIN, GREEN_MAX)
    zebra_crossings.append([z_pos, "GREEN", green_time, green_time])

def spawn_pedestrians_for_crossing(z_pos, zc_id):
    count = random.randint(1, 2)
    for _ in range(count):
        from_left = random.choice([True, False])
        start_x = -ROAD_HALF_WIDTH + 15 if from_left else ROAD_HALF_WIDTH - 15
        pedestrians.append({
            "x": start_x, "y": PED_Y, "z": z_pos + random.uniform(-10, 10),
            "dir": 1 if from_left else -1, "zc_id": zc_id
        })

# Entity Updates
def update_traffic_cars():
    for car in traffic_cars:
        next_z = car[2] + car[3] * 2
        blocked = False
        if not blocked: car[2] = next_z
        car[1] = get_road_y(car[2])  
        for zc in zebra_crossings:
            if zc[1] != "RED": continue
            stop_line = zc[0] - 80
            if car[2] < stop_line and next_z >= stop_line: car[2] = stop_line; blocked = True; break
            if stop_line <= car[2] < zc[0]-40: car[2] = stop_line; blocked = True; break

def update_ramps():
    global ramps, is_jumping, player_vel_y, player_speed
    new_ramps = []
    for r in ramps:
        if abs(player_pos[0] - r[0]) < 25: 
            if r[2] - 40 < player_pos[2] < r[2] + 10:
                if not is_jumping:
                    is_jumping = True
                    base_lift = 5.0 
                    lift_multiplier = abs(player_speed) * 8.0 
                    player_vel_y = base_lift + lift_multiplier
                    if player_speed < 0: player_speed *= 1.2 
                    print(f"JUMP!")
        if r[2] < player_pos[2] + 200:
             new_ramps.append(r)
    ramps = new_ramps

def update_zebra_crossings():
    global zebra_crossings
    for zc in zebra_crossings:
        zc[2] -= 1
        if zc[2] > 0: continue
        if zc[1] == "GREEN":
            zc[1] = "RED"; zc[2] = RED_FRAMES
            spawn_pedestrians_for_crossing(zc[0], id(zc))
        else:
            zc[1] = "GREEN"; zc[2] = random.randint(GREEN_MIN, GREEN_MAX)

def update_pedestrians():
    global pedestrians
    new_list = []
    for p in pedestrians:
        if isinstance(p, dict):
            p.setdefault("state", "WALK"); p.setdefault("ttl", 0); p.setdefault("dir", 1)
        else: continue
        
        if p["state"] == "WALK":
            p["x"] += p["dir"] * PED_SPEED
            if p["x"] < -ROAD_HALF_WIDTH - 30 or p["x"] > ROAD_HALF_WIDTH + 30: continue
        elif p["state"] == "FALL":
            p["ttl"] -= 1
            if p["ttl"] <= 0: continue
        new_list.append(p)
    pedestrians = new_list

def update_magnet_powerup():
    global magnet_active, magnet_timer
    if magnet_active:
        magnet_timer -= 1
        if magnet_timer <= 0: magnet_active = False; return
        for coin in point_objects:
            dx = player_pos[0] - coin[0]; dz = player_pos[2] - coin[2]
            if math.sqrt(dx*dx + dz*dz) < 500 and coin[2] < player_pos[2] + 50:
                coin[0] += dx * 0.15; coin[2] += dz * 0.15

def update_grenades():
    global grenades, traffic_cars, static_obstacles, score
    for g in grenades[:]:
        pos, vel, life = g
        pos[0] += vel[0]; pos[1] += vel[1]; pos[2] += vel[2]
        g[2] -= 1
        if g[2] <= 0: grenades.remove(g); continue

        hit = False
        blast = 40
        for car in traffic_cars[:]:
            if math.sqrt((pos[0] - car[0])**2 + (pos[2] - car[2])**2) < blast:
                car[4] -= 1
                if car[4] <= 0: traffic_cars.remove(car); 
                score += 5
                print(f"Score: {score}")
                hit = True; 
                break
        if not hit:
            for obs in static_obstacles[:]:
                if math.sqrt((pos[0] - obs[0])**2 + (pos[2] - obs[2])**2) < blast:
                    static_obstacles.remove(obs); 
                    score += 2
                    print(f"Score: {score}")
                    hit = True; 
                    break
        if hit: 
            grenades.remove(g)

# grenade
def fire_grenade():
    global grenade_cooldown
    if grenade_cooldown > 0: return
    start = list(player_pos); start[1] = 20
    grenades.append([start, [0, 0, -GRENADE_SPEED * 2.0], GRENADE_LIFETIME])
    grenade_cooldown = 20

def auto_defense_shoot():
    if not cheat_mode: return
    closest_z = None; shots = 0
    for car in traffic_cars:
        dz = player_pos[2] - car[2]
        if 0 < dz < 350 and abs(car[0] - player_pos[0]) < 25:
            if closest_z is None or dz < closest_z: closest_z = dz; shots = max(shots, car[4])
    if closest_z is None:
        for obs in static_obstacles:
            dz = player_pos[2] - obs[2]
            if 0 < dz < 350 and abs(obs[0] - player_pos[0]) < 25:
                if closest_z is None or dz < closest_z: closest_z = dz; shots = 1
    if closest_z:
        for _ in range(shots): fire_grenade()

#auto driving
def get_lane_safety_score(lane_idx):
    check_x = (lane_idx - 1) * LANE_WIDTH
    min_dist = 2000 
    for car in traffic_cars:
        if abs(car[0] - check_x) < 20 and (player_pos[2] - car[2] > 0): 
            min_dist = min(min_dist, player_pos[2] - car[2])
    for obs in static_obstacles:
        if abs(obs[0] - check_x) < 20 and (player_pos[2] - obs[2] > 0): 
            min_dist = min(min_dist, player_pos[2] - obs[2])
    return min_dist

def run_auto_drive_ai():
    global player_lane, ai_cooldown
    if ai_cooldown > 0: 
        ai_cooldown -= 1; 
        return
    curr = get_lane_safety_score(player_lane)
    left = get_lane_safety_score(player_lane - 1) if player_lane > 0 else -1
    right = get_lane_safety_score(player_lane + 1) if player_lane < 2 else -1
    if curr < 400:
        if left > curr and left >= right: player_lane -= 1; ai_cooldown = 15
        elif right > curr and right > left: player_lane += 1; ai_cooldown = 15

def check_collisions():
    global game_over, car_damage_level, hood_angle, score, player_speed, is_jumping, player_vel_y
    global last_red_zebra_fined
    player_box = (player_pos[0], player_pos[2])

    for zc in zebra_crossings:
        if zc[1] != "RED": continue
        if abs(player_pos[2] - zc[0]) <= ZEBRA_ZONE_HALF_LEN:
            if last_red_zebra_fined != zc[0]:
                score -= 10
                print(f"Score: {score}")
                last_red_zebra_fined = zc[0]
            break
    
    on_any_red_zebra = any((zc[1] == "RED" and abs(player_pos[2] - zc[0]) <= ZEBRA_ZONE_HALF_LEN) for zc in zebra_crossings)
    if not on_any_red_zebra: last_red_zebra_fined = None

    PLAYER_HIT_RADIUS = 22
    PED_HIT_RADIUS = 16
    for p in pedestrians:
        if p["state"] != "WALK": continue
        dx = player_pos[0] - p["x"]
        dz = player_pos[2] - p["z"]
        if math.sqrt(dx*dx + dz*dz) < (PLAYER_HIT_RADIUS + PED_HIT_RADIUS):
            score -= 20
            print(f"Score: {score}")
            p["state"] = "FALL"
            p["ttl"] = PED_DESPAWN_FRAMES
            p["y"] = 2
            break

    for coin in point_objects[:]:
        if math.sqrt((player_pos[0] - coin[0])**2 + (player_pos[2] - coin[2])**2) < 30:
            point_objects.remove(coin)
            score += 10
            print(f"Score: {score}")

    all_hazards = []
    for car in traffic_cars: all_hazards.append((car[0], car[2], 30))
    for obs in static_obstacles: all_hazards.append((obs[0], obs[2], 25))

    if not cheat_mode:
        for hx, hz, radius in all_hazards:
            if math.sqrt((player_box[0] - hx)**2 + (player_box[1] - hz)**2) < radius:
                car_damage_level += 1
                hood_angle = min(hood_angle + 30, 90)
                player_speed = -0.5 
                if player_pos[0] > hx: player_pos[0] += 5
                else: player_pos[0] -= 5
                if car_damage_level >= 3: game_over = True

#Update Loop

def update_world():
    global player_pos, player_speed, wheel_rotation, distance_travelled
    global game_over, earthquake_timer, earthquake_intensity
    global player_vel_y, is_jumping, grenade_cooldown 
    global frame_counter

    if game_over: return

    frame_counter += 1

    CRUISE_SPEED = 0.4 
    if player_speed < CRUISE_SPEED: player_speed += 0.01
    elif player_speed > CRUISE_SPEED: player_speed -= 0.01
    if player_speed < -0.5: player_speed = -0.5

    player_pos[2] -= player_speed * 5
    distance_travelled += abs(player_speed)
    wheel_rotation += player_speed * 20
    
    spawn_zebra_crossing_if_needed()

    target_x = (player_lane - 1) * LANE_WIDTH
    player_pos[0] += (target_x - player_pos[0]) * 0.1

    ground_y = get_road_y(player_pos[2])
    
    if is_jumping:
        GRAVITY = 0.5
        player_pos[1] += player_vel_y
        player_vel_y -= GRAVITY
        ground_y = get_road_y(player_pos[2])
        if player_pos[1] <= ground_y:
            player_pos[1] = ground_y
            player_vel_y = 0
            is_jumping = False
    else:
        player_pos[1] = ground_y

    if earthquake_timer > 0:
        earthquake_timer -= 1
        earthquake_intensity = 4.0
    else:
        earthquake_intensity = 0.0

    spawn_entities()
    spawn_bridge_if_needed()
    spawn_ramp_if_needed()

    if grenade_cooldown > 0: grenade_cooldown -= 1

    update_traffic_cars()
    update_grenades()
    update_ramps()
    update_zebra_crossings()
    update_pedestrians()
    update_magnet_powerup()
    
    if auto_drive_mode: run_auto_drive_ai()
    auto_defense_shoot()
    check_collisions()

    glutPostRedisplay()

##drawings

# Draw Car
def draw_detailed_car(x, y, z, color_body, is_player=False):
    glPushMatrix()
    glTranslatef(x, y + 5, z) 
    glRotatef(player_rotation if is_player else 0, 0, 1, 0)
    
    #damage logic
    damage = car_damage_level if is_player else 0
   
    #color darkening
    current_color = list(color_body)
    if damage > 0:
        darken_factor = damage * 0.2
        current_color[0] = max(0.2, current_color[0] - darken_factor)
        current_color[1] = max(0.1, current_color[1] - darken_factor/2)
        current_color[2] = max(0.1, current_color[2] - darken_factor/2)
    #main chassis
    glColor3f(current_color[0], current_color[1], current_color[2])
    glPushMatrix()
    glScalef(1.2, 0.3, 2.5)
    glutSolidCube(20)
    glPopMatrix()
    
    #cabin displaced
    glColor3f(0.0, 0.0, 0.0) 
    glPushMatrix()
    if damage >= 2:
        glTranslatef(2, 5, 2)
        glRotatef(15, 0, 1, 0)
        glRotatef(5, 1, 0, 0)
    else:
        glTranslatef(0, 5, 2)
    glScalef(0.9, 0.25, 1.2)
    glutSolidCube(20)
    glPopMatrix()
    
    if is_player:
        glColor3f(0, 0, 0)
        glPushMatrix()
        glTranslatef(0, 8, 22)
        glScalef(1.4, 0.1, 0.5)
        glutSolidCube(20)
        glPopMatrix()

    #Headlights
    glPushMatrix()
    glTranslatef(-8, 0, -24)
    if damage >= 1: glColor3f(0.1, 0.1, 0.1) 
    else: glColor3f(1.0, 1.0, 0.8) 
    draw_sphere(2, 8, 8) 
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(8, 0, -24)
    glColor3f(1.0, 1.0, 0.8) 
    draw_sphere(2, 8, 8)
    glPopMatrix()

    #Wheels
    glColor3f(0.1, 0.1, 0.1) 
    wheel_positions = [(-12, -4, 12), (12, -4, 12), (-12, -4, -15), (12, -4, -15)]
    

    current_rot = wheel_rotation if is_player else (frame_counter * 15)

    for i, (wx, wy, wz) in enumerate(wheel_positions):
        glPushMatrix()
        glTranslatef(wx, wy, wz)
        glRotatef(current_rot, 1, 0, 0) # Rotate around
        glRotatef(90, 0, 1, 0)          # Face outward
        
        # tire
        glColor3f(0.1, 0.1, 0.1) 
        if i % 2 == 0: 
             draw_cylinder(4.0, 4.0, 12) 
        else: 
             glPushMatrix()
             glTranslatef(0, 0, -4.0)
             draw_cylinder(4.0, 4.0, 12)
             glPopMatrix()
        
        glColor3f(0.5, 0.5, 0.5) 
        offset = -0.1 if i % 2 == 0 else 0.1
        
        glPushMatrix()
        glTranslatef(0, 0, offset)
        
        #Rim Circle
        glPushMatrix()
        glScalef(1, 1, 0.1)
        draw_cylinder(2.5, 1.0, 10)
        glPopMatrix()

        #Cross
        glColor3f(0.8, 0.8, 0.8) 
        
        # Horizontal Bar
        glPushMatrix()
        glScalef(3.5, 0.8, 0.2) 
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Vertical Bar
        glPushMatrix()
        glScalef(0.8, 3.5, 0.2) 
        glutSolidCube(1.0)
        glPopMatrix()

        glPopMatrix() 
        
        glPopMatrix() 
    #damage visuals particles
    if is_player and damage > 0:
        time_val = frame_counter * 0.1 
        num_particles = damage * 5 
        for i in range(num_particles):
            glPushMatrix()
            offset_val = (time_val + i * 0.2) % 3.0
            sx = math.sin(time_val * 5 + i) * 3
            sz = math.cos(time_val * 3 + i) * 3 - 20 
            sy = 10 + (offset_val * 15) 
            glTranslatef(sx, sy, sz)
            if damage == 3 and i % 3 == 0:
                glColor3f(1.0, random.uniform(0.0, 0.6), 0.0)
                size = 3.0 - offset_val 
            else:
                grey = 0.4 - (offset_val * 0.1)
                glColor3f(grey, grey, grey)
                size = 2.0 + offset_val * 2 
            glutSolidCube(size)
            glPopMatrix()

    glPopMatrix()

def draw_player_car():
    draw_detailed_car(player_pos[0], player_pos[1], player_pos[2], [0.9, 0.1, 0.1], is_player=True)

def draw_traffic_car(car_data):
    draw_detailed_car(car_data[0], car_data[1] + 5, car_data[2], [0.2, 0.5, 0.8], is_player=False)

# Draw road and env
def draw_road_and_world():
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex3f(-200, 0, player_pos[2] - 2000)
    glVertex3f(200, 0, player_pos[2] - 2000)
    glVertex3f(200, 0, player_pos[2] + 500)
    glVertex3f(-200, 0, player_pos[2] + 500)
    glEnd()
    
    glColor3f(1, 1, 0)
    glLineWidth(2)
    glBegin(GL_LINES)
    start_z = int(player_pos[2]) - 2000
    end_z = int(player_pos[2]) + 500
    for z in range(start_z, end_z, 60):
        for lane_x in [-LANE_WIDTH / 2, LANE_WIDTH / 2]:
            glVertex3f(lane_x, 0.5, z)
            glVertex3f(lane_x, 0.5, z + 30)
    glEnd()

    block_size = 300
    current_block = int(player_pos[2] / block_size)

    for i in range(current_block + 2, current_block - 15, -1):
        z_pos = i * block_size
        on_bridge = False
        for (b_start, b_end) in bridges:
            s = max(b_start, b_end) + 50 
            e = min(b_start, b_end) - 50
            if z_pos <= s and z_pos >= e:
                on_bridge = True
                break
        if on_bridge: continue

        if theme == "urban":
            height = 100 + (abs(i * 37) % 150)
            glPushMatrix()
            glTranslatef(-300, height / 2, z_pos)
            glColor3f(0.5, 0.5, 0.6)
            glScalef(1, height / 50, 1)
            glutSolidCube(100)
            if i % 2 == 0:
                glPushMatrix()
                glColor3f(1, 1, 0)
                glTranslatef(51, 0, 0)
                glScalef(0.1, 0.8, 0.6)
                glutSolidCube(100)
                glPopMatrix()
            glPopMatrix()

            glPushMatrix()
            glTranslatef(300, height / 2, z_pos)
            glColor3f(0.6, 0.5, 0.5)
            glScalef(1, height / 50, 1)
            glutSolidCube(100)
            glPopMatrix()
        else:
            for x_offset in [-280, 280]:
                glPushMatrix()
                glTranslatef(x_offset, 0, z_pos)
                glColor3f(0.4, 0.2, 0.1)
                glPushMatrix()
                glScalef(1, 5, 1)
                glRotatef(-90, 1, 0, 0)
                draw_cylinder(10, 20, 10) 
                glPopMatrix()
                glColor3f(0.1, 0.6, 0.1)
                glTranslatef(0, 60, 0)
                glRotatef(-90, 1, 0, 0)
                draw_cone(40, 80, 10) 
                glPopMatrix()
#draw bridges
def drawbridges():
    global bridges
    DECK_THICKNESS = 10.0
    BARRIER_HEIGHT = 12.0
    BARRIER_WIDTH = 8.0
    PILLAR_SPACING = 120.0
    
    for (z_start, z_end) in bridges:
        start = max(z_start, z_end)
        end = min(z_start, z_end)
        step_size = 25.0
        z = start
        while z > end:
            curr_z = z
            next_z = max(z - step_size, end)
            y1 = get_road_y(curr_z)
            y2 = get_road_y(next_z)
            
            glColor3f(0.5, 0.5, 0.55)
            glBegin(GL_QUADS)
            glVertex3f(-BRIDGEWIDTH, y1, curr_z)
            glVertex3f(BRIDGEWIDTH, y1, curr_z)
            glVertex3f(BRIDGEWIDTH, y2, next_z)
            glVertex3f(-BRIDGEWIDTH, y2, next_z)
            glVertex3f(-BRIDGEWIDTH+10, y1-10, curr_z)
            glVertex3f(BRIDGEWIDTH-10, y1-10, curr_z)
            glVertex3f(BRIDGEWIDTH-10, y2-10, next_z)
            glVertex3f(-BRIDGEWIDTH+10, y2-10, next_z)
            glVertex3f(-BRIDGEWIDTH, y1, curr_z)
            glVertex3f(-BRIDGEWIDTH+10, y1-10, curr_z)
            glVertex3f(-BRIDGEWIDTH+10, y2-10, next_z)
            glVertex3f(-BRIDGEWIDTH, y2, next_z)
            glVertex3f(BRIDGEWIDTH, y1, curr_z)
            glVertex3f(BRIDGEWIDTH-10, y1-10, curr_z)
            glVertex3f(BRIDGEWIDTH-10, y2-10, next_z)
            glVertex3f(BRIDGEWIDTH, y2, next_z)
            glEnd()
            
            glColor3f(0.2, 0.2, 0.22)
            road_w = BRIDGEWIDTH - BARRIER_WIDTH
            glBegin(GL_QUADS)
            glVertex3f(-road_w, y1 + 0.2, curr_z)
            glVertex3f(road_w, y1 + 0.2, curr_z)
            glVertex3f(road_w, y2 + 0.2, next_z)
            glVertex3f(-road_w, y2 + 0.2, next_z)
            glEnd()
            z -= step_size

        current_pillar_z = start - 50
        while current_pillar_z > end + 50:
            h = get_road_y(current_pillar_z)
            if h > 15:
                glColor3f(0.45, 0.45, 0.5)
                glPushMatrix()
                glTranslatef(0, 0, current_pillar_z)
                glRotatef(-90, 1, 0, 0)
                draw_cylinder(15, h - DECK_THICKNESS, 12) 
                glPopMatrix()
                glColor3f(0.4, 0.4, 0.45)
                glPushMatrix()
                glTranslatef(0, h - DECK_THICKNESS - 5, current_pillar_z)
                glScalef(BRIDGEWIDTH * 1.5, 10, 50)
                glutSolidCube(1.0)
                glPopMatrix()
            current_pillar_z -= PILLAR_SPACING
#draw ramps
def draw_ramps():
    for r in ramps:
        width, length, height = 24.0, 40.0, 8.0
        glPushMatrix()
        glTranslatef(r[0], r[1], r[2])
        glColor3f(0.5, 0.5, 0.5) 
        glBegin(GL_TRIANGLES)
        glVertex3f(-width/2, 0, 0); glVertex3f(-width/2, height, -length); glVertex3f(-width/2, 0, -length)
        glVertex3f(width/2, 0, 0); glVertex3f(width/2, height, -length); glVertex3f(width/2, 0, -length)
        glEnd()
        glBegin(GL_QUADS)
        glVertex3f(-width/2, 0, 0); glVertex3f(width/2, 0, 0); glVertex3f(width/2, height, -length); glVertex3f(-width/2, height, -length)
        glVertex3f(-width/2, 0, -length); glVertex3f(width/2, 0, -length); glVertex3f(width/2, height, -length); glVertex3f(-width/2, height, -length)
        glEnd()
        glPopMatrix()

# Draw Objects
def draw_grenades():
    glColor3f(0.2, 0.4, 0.2)
    for g in grenades:
        glPushMatrix()
        glTranslatef(g[0][0], g[0][1], g[0][2])
        draw_sphere(5, 8, 8)
        glPopMatrix()

def draw_gameplay_objects():
    glColor3f(1.0, 0.8, 0.0)
    rotation = frame_counter * 5.0 
    for coin in point_objects:
        glPushMatrix()
        glTranslatef(coin[0], coin[1], coin[2])
        glRotatef(rotation, 0, 1, 0) 
        draw_cylinder(5, 1, 12)
        glPopMatrix()
    
    glColor3f(1.0, 0.5, 0.0)
    for obs in static_obstacles:
        glPushMatrix()
        glTranslatef(obs[0], obs[1], obs[2])
        glutSolidCube(20)
        glPopMatrix()
    
    glColor3f(0.9, 0.1, 0.1)
    for obs in moving_obstacles:
        glPushMatrix()
        glTranslatef(obs[0], obs[1], obs[2])
        glutSolidCube(30)
        glPopMatrix()
    
    glColor3f(0.2, 0.2, 0.8)
    for mag in magnet_pos:
        glPushMatrix()
        glTranslatef(mag[0], mag[1], mag[2])
        glutSolidCube(15)
        glPopMatrix()

# Draw Zebra
def draw_zebra_crossing():
    road_half_width = 200
    stripe_width = 4
    gap_width = 6
    num_stripes = 12
    y = 0.6
    for zc in zebra_crossings:
        z_center = zc[0]
        total_len = num_stripes * stripe_width + (num_stripes - 1) * gap_width
        z_start = z_center - total_len / 2.0
        glColor3f(1, 1, 1)
        for i in range(num_stripes):
            z0 = z_start + i * (stripe_width + gap_width)
            z1 = z0 + stripe_width
            glBegin(GL_QUADS)
            glVertex3f(-road_half_width + 10, y, z0)
            glVertex3f( road_half_width - 10, y, z0)
            glVertex3f( road_half_width - 10, y, z1)
            glVertex3f(-road_half_width + 10, y, z1)
            glEnd()
        glPushMatrix()
        glTranslatef(road_half_width + 40, 50, z_center)
        if zc[1] == 'RED': glColor3f(1, 0, 0)
        else: glColor3f(0.3, 0, 0)
        draw_sphere(10, 10, 10)
        glTranslatef(0, -25, 0)
        if zc[1] == 'GREEN': glColor3f(0, 1, 0)
        else: glColor3f(0, 0.3, 0)
        draw_sphere(10, 10, 10)
        glPopMatrix()

def draw_human(x, y, z, walk_phase=0.0, facing_dir=1):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(90 if facing_dir > 0 else -90, 0, 1, 0)
    glScalef(0.8, 0.8, 0.8)
    leg_ang = math.sin(walk_phase) * 35
    arm_ang = -math.sin(walk_phase) * 30
    
    glColor3f(0.2, 0.4, 0.9)
    glPushMatrix()
    glTranslatef(0, 18, 0)
    glScalef(1.2, 1.6, 0.6)
    glutSolidCube(10)
    glPopMatrix()
    
    glColor3f(0.9, 0.8, 0.7)
    glPushMatrix()
    glTranslatef(0, 30, 0)
    draw_sphere(5, 10, 10) 
    glPopMatrix()
    
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(-3, 8, 0)
    glRotatef(leg_ang, 1, 0, 0)
    glTranslatef(0, -6, 0)
    glScalef(0.4, 1.2, 0.4)
    glutSolidCube(10)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(3, 8, 0)
    glRotatef(-leg_ang, 1, 0, 0)
    glTranslatef(0, -6, 0)
    glScalef(0.4, 1.2, 0.4)
    glutSolidCube(10)
    glPopMatrix()
    
    glColor3f(0.9, 0.8, 0.7)
    glPushMatrix()
    glTranslatef(-8, 20, 0)
    glRotatef(arm_ang, 1, 0, 0)
    glTranslatef(0, -5, 0)
    glScalef(0.35, 1.1, 0.35)
    glutSolidCube(10)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(8, 20, 0)
    glRotatef(-arm_ang, 1, 0, 0)
    glTranslatef(0, -5, 0)
    glScalef(0.35, 1.1, 0.35)
    glutSolidCube(10)
    glPopMatrix()
    glPopMatrix()

def draw_pedestrians():
    t = frame_counter * 0.15 
    for p in pedestrians:
        p.setdefault("state", "WALK")
        p.setdefault("dir", 1)
        glPushMatrix()
        glTranslatef(p["x"], p["y"], p["z"])
        if p["state"] == "FALL": glRotatef(90, 0, 0, 1)
        phase = t + (p["z"] * 0.05)
        draw_human(0, 0, 0, walk_phase=phase, facing_dir=p["dir"])
        glPopMatrix()

# Camera
def setup_camera():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(60, (WINDOW_WIDTH / WINDOW_HEIGHT), 0.1, 5000.0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    sx = (random.random() - 0.5) * earthquake_intensity
    sy = (random.random() - 0.5) * earthquake_intensity
    if camera_view_mode == 0:
        ex = player_pos[0] + camera_distance * math.sin(math.radians(camera_angle))
        ez = player_pos[2] + camera_distance * math.cos(math.radians(camera_angle))
        gluLookAt(ex + sx, sy + camera_height, ez, player_pos[0], 50, player_pos[2], 0, 1, 0)
    elif camera_view_mode == 1:
        gluLookAt(player_pos[0] + sx, player_pos[1] + 30 + sy, player_pos[2] - 10, player_pos[0], player_pos[1] + 30, player_pos[2] - 100, 0, 1, 0)
    elif camera_view_mode == 2:
        gluLookAt(player_pos[0], 500, player_pos[2], player_pos[0], 0, player_pos[2], 0, 0, -1)

#Display
def display():
    setup_camera()
    if is_day:
        glClearColor(0.5, 0.8, 1.0, 1.0)  # Blue Sky
    else:
        glClearColor(0.05, 0.05, 0.12, 1.0) # Dark Night

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    draw_road_and_world()
    drawbridges()
    draw_ramps()
    draw_player_car()
    for car in traffic_cars: draw_traffic_car(car)
    draw_grenades()
    draw_gameplay_objects()
    draw_zebra_crossing()
    draw_pedestrians()
    
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    
    if game_over:
        draw_text(WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT/2, "GAME OVER")
        draw_text(WINDOW_WIDTH/2 - 60, WINDOW_HEIGHT/2 - 30, f"Final Score: {score}")
    else:
        lives = max(0, 3 - car_damage_level)
        if lives == 3: glColor3f(0, 1, 0)
        elif lives == 2: glColor3f(1, 1, 0)
        else: glColor3f(1, 0, 0)
        draw_text(20, WINDOW_HEIGHT - 40, f"LIVES: {lives}")
        glColor3f(1, 1, 1)
        draw_text(20, WINDOW_HEIGHT - 70, f"SCORE: {score}")
        draw_text(20, WINDOW_HEIGHT - 100, f"DISTANCE: {int(distance_travelled)}") 
        draw_text(20, WINDOW_HEIGHT - 130, f"SPEED: {player_speed:.2f}")

    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)
    glutSwapBuffers()


# Input Handling
def keyboard(key, x, y):
    global player_speed, player_lane, cheat_mode, auto_drive_mode, theme, is_day, earthquake_timer, camera_view_mode, magnet_active, magnet_timer
    key = key.decode("utf-8").lower()
    if key == 'w':
        player_speed = min(MAX_SPEED, player_speed + ACCELERATION)
    elif key == 's':
        player_speed = max(-MAX_SPEED / 2, player_speed - ACCELERATION)
    elif key == 'a':
        player_lane = max(0, player_lane - 1)
    elif key == 'd':
        player_lane = min(2, player_lane + 1)
    elif key == 'c':
        global camera_view_mode
        camera_view_mode = (camera_view_mode + 1) % 3
    elif key == 'k':
        cheat_mode = not cheat_mode
        print(f"Cheat Mode: {'ON' if cheat_mode else 'OFF'}")
    elif key == 't': 
        theme = "rural" if theme == "urban" else "urban"
    elif key == 'n': 
        is_day = not is_day
    elif key == 'e': 
        earthquake_timer = 120
    elif key == ' ':
        fire_grenade()
    elif key == 'm': 
        global magnet_active, magnet_timer
        magnet_active = True
        magnet_timer = MAGNET_DURATION
    elif key == 'p':
        auto_drive_mode = not auto_drive_mode
        print(f"Auto-Drive: {'ON' if auto_drive_mode else 'OFF'}")
    elif key == 'r':
        reset_game()
def special_keys(key, x, y):
    global camera_angle, camera_distance
    if key == GLUT_KEY_LEFT: camera_angle -= 5
    elif key == GLUT_KEY_RIGHT: camera_angle += 5
    elif key == GLUT_KEY_UP: camera_distance -= 10
    elif key == GLUT_KEY_DOWN: camera_distance += 10

def reset_game():
    global player_pos, player_speed, player_lane, wheel_rotation, game_over, score, distance_travelled
    global traffic_cars, point_objects, static_obstacles, moving_obstacles, grenades, car_damage_level, hood_angle
    global next_zebra_distance, zebra_crossings
    next_zebra_distance = 500; zebra_crossings = []
    player_pos = [0, 0, 0]; player_speed = 0.0; player_lane = 1; wheel_rotation = 0
    car_damage_level = 0; hood_angle = 0; game_over = False; score = 0; distance_travelled = 0
    traffic_cars = []; point_objects = []; static_obstacles = []; moving_obstacles = []; grenades = []
    print("Game Restarted!")

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"Highway Car Rush")

    glEnable(GL_DEPTH_TEST)
    
    ramps.append([0, 0, player_pos[2] - 500]) 
    
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutIdleFunc(update_world)

    print("Controls:")
    print("  W/S: Accelerate/Brake")
    print("  A/D: Switch Lanes")
    print("  C: Change Camera")
    print("  T: Switch Theme (Urban/Rural)")
    print("  N: Toggle Day/Night")
    print("  E: Trigger Earthquake")
    print("  K: Toggle Cheat Mode")
    print("  Space: Fire Grenade")
    print("  M: Activate Magnet")
    print("  P: Toggle Auto-Drive")

    glutMainLoop()

if __name__ == "__main__":
    main()
