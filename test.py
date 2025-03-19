print("Hello, world!")
print("Python is working!")

# Try to display available Python packages
try:
    import pkg_resources
    installed_packages = pkg_resources.working_set
    installed_packages_list = sorted(["%s==%s" % (i.key, i.version) for i in installed_packages])
    print("Installed packages:")
    for pkg in installed_packages_list:
        print(pkg)
except Exception as e:
    print(f"Error listing packages: {e}")