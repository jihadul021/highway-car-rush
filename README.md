# 🚗 Highway Car Rush

**Highway Car Rush** is a 3D driving game featuring realistic car mechanics, dynamic environments, and arcade combat elements. Built entirely from scratch using **Python** and **OpenGL**, it demonstrates complex graphics programming concepts without relying on pre-made game engines.

## 📖 Description

Highway Car Rush is a driving game featuring realistic car mechanics, including rotating wheels, physical damage visuals, and stunt capabilities like parabolic ramp jumps. Players navigate dynamic urban and rural environments with day-night cycles, surviving hazards like earthquakes and utilizing explosive grenades to clear obstacles. The game integrates complex traffic rules—such as functional traffic lights with pedestrian crossings and penalizing collisions—alongside helpful power-ups like coin magnets and an assisted "Auto Drive" mode. With a 360-degree camera view and cheat options, it combines arcade action with rich simulation elements.

---

## ✨ Features & Implementation Details

### 🏎️ Vehicle Mechanics & Physics
*   **Detailed 3D Car Models:** Custom-built player and traffic cars using OpenGL primitives.
*   **Dynamic Wheel Rotation:** Wheels spin faster or slower corresponding to the car's actual velocity.
*   **Physical Damage System:**
    *   Visual deformation logic (hood pops open, body color darkens).
    *   Particle effects (smoke) appear based on damage severity.
*   **Parabolic Stunt Jumps:** Physics-based gravity calculation for realistic flight trajectories off ramps.
*   **Grenade Launcher:** Projectile weapon system that destroys obstacles and clears lanes with visual impact.

### 🌍 World, Environment & Camera
*   **Procedural Road Generation:** Infinite 3D road with slopes, lanes, and elevated bridges.
*   **Dynamic Themes:** Toggleable environments between **Urban** (skyscrapers with lit windows) and **Rural** (trees and nature).
*   **Day/Night Cycle:** Real-time lighting changes affecting sky color and visibility.
*   **Camera Systems:** Multiple perspectives including Cockpit view, Top-down view, and a fully rotatable **360° Orbit Camera**.
*   **Earthquake Event:** Random hazard event that shakes the camera and increases difficulty.
*   **Cheat Mode:** Dev-tool toggle for invincibility (disables Game Over) while maintaining scoring mechanics.

### 🤖 AI, Traffic & Gameplay Logic
*   **Smart Traffic System:** AI cars obey traffic laws, stopping at Red lights and yielding to pedestrians.
*   **Pedestrian Crossing:** Fully animated 3D humans cross the road at zebra crossings during red lights.
*   **Penalty System:** Logic to deduct points for running red lights or hitting pedestrians (complete with "falling" animations).
*   **Interactive Objects:** 3D Coins for points and Static Barriers for hazards.
*   **Magnet Power-up:** Special item that automatically attracts nearby coins to the player.
*   **Auto-Drive Mode:** An AI copilot that automatically switches lanes to dodge obstacles based on a safety-score algorithm.

---

## 🎮 Controls

| Key | Action |
| :--- | :--- |
| **W** | Accelerate |
| **S** | Brake / Reverse |
| **A / D** | Switch Lanes (Left / Right) |
| **SPACE** | Fire Grenade Launcher |
| **C** | Change Camera View |
| **N** | Toggle Day / Night |
| **T** | Switch Theme (City / Rural) |
| **P** | Toggle Auto-Drive AI |
| **M** | Activate Magnet Powerup |
| **K** | Toggle Cheat Mode |
| **E** | Trigger Earthquake |
| **R** | Reset Game |
