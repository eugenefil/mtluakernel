This Python package is meant as a complement to [mtluarunner](https://github.com/eugenefil/mtluarunner) Minetest mod.

# Install with pipx

Install Jupyter:

```sh
pipx install --include-deps jupyter
```

Inject this package into Jupyter virtual environment created by pipx:

```sh
git clone https://github.com/eugenefil/mtluakernel
pipx inject jupyter ./mtluakernel
```

Register Minetest Lua kernel with Jupyter:

```sh
jupyter kernelspec install ./mtluakernel/mtlua --user
```

# Run

Start Jupyter notebook server:

```sh
jupyter notebook
```

Create new notebook by clicking New -> Notebook. In the "Select Kernel" dialogue choose "Minetest Lua".

Start Minetest. Create and start a world with the [mtluarunner](https://github.com/eugenefil/mtluarunner) mod enabled. To test connection to Minetest execute the following Lua code in a notebook cell:

```lua
print(minetest.get_version())
```

If output containing Minetest version is printed in response, everything's fine.
