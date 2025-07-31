# Windows Defender Antivirus Exclusions

This document tracks the Windows Defender exclusions added for optimal Dart & Flutter development performance.

## Background
Windows Defender can significantly slow down Dart & Flutter development by scanning:
- Package cache directories
- Build outputs  
- SDK files
- Project files during compilation

Adding exclusions prevents unnecessary scanning and improves build performance.

## Added Exclusions

### Date: [To be filled when exclusions are added]

**Exclusion Paths Added:**

1. **Pub Cache Directory**
   - Path: `%USERPROFILE%\AppData\Local\Pub\Cache`
   - Purpose: Dart/Flutter package cache - frequently accessed during builds

2. **Pub Directory** 
   - Path: `%USERPROFILE%\AppData\Local\Pub`
   - Purpose: Pub tool directory and related files

3. **Flutter SDK Directory**
   - Path: `%USERPROFILE%\flutter` (or actual SDK location)
   - Purpose: Flutter SDK installation directory

4. **Project Root Directory**
   - Path: `D:\projects\2025\bruno_ai_v2\client`
   - Purpose: Current project directory with frequent file changes during development

## Steps Taken

### Adding Exclusions
1. Open Windows Security
2. Navigate to "Virus & threat protection"
3. Click "Manage settings" under "Virus & threat protection settings"
4. Scroll down to "Exclusions" section
5. Click "Add or remove exclusions"
6. Click "Add an exclusion" → "Folder"
7. Add each path listed above

### Service Restart
After adding exclusions:
- Restart "Microsoft Defender Antivirus Service" OR
- Reboot system to ensure changes take effect

## Verification
- [ ] All exclusion paths added successfully
- [ ] Microsoft Defender Antivirus Service restarted
- [ ] Build performance improved (subjective test)

## Notes
- These exclusions are specific to this development machine
- Review periodically for security considerations
- Remove exclusions if project is no longer active
