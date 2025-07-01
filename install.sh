#!/bin/bash
echo "Installing RPyFrame service..."
echo ""
echo "Creating directories and copying files..."
cp -v main.py ~/.local/bin/main.py
mkdir -vp ~/.config/rpyframe
cp -v config.json ~/.config/rpyframe/config.json
mkdir -vp ~/.config/systemd/user
cp -v rpyframe.service ~/.config/systemd/user/rpyframe.service

echo "Starting RPyFrame service..."
systemctl --user daemon-reload
systemctl --user enable rpyframe.service
systemctl --user start rpyframe.service

echo ""
echo "RPyFrame service installed and started."
echo "- You can check the status with: systemctl --user status rpyframe.service"
echo "- To stop the service, use: systemctl --user stop rpyframe.service"
echo "- To disable the service, use: systemctl --user disable rpyframe.service"
echo "- To view logs, use: journalctl --user -u rpyframe.service"
echo "- Make sure to adjust the IMAGE_FOLDER in config.json if needed."
echo "- You can edit the config.json file to change settings."
echo "- Configuration file is located at: ~/.config/rpyframe/config.json"
echo "- If you need to change the Python environment, modify the ExecStart line in rpyframe.service"
echo ""
echo "For more information, visit the RPyFrame repository."
echo "Thank you for using RPyFrame!"
echo "If you encounter any issues, please check the logs or open an issue on the repository."
echo "Have a great day!"