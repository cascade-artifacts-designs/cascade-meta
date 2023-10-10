# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

PYTHON=python3.9

RUSTEXEC=$(CARGO_HOME)/bin/rustc
RUSTUPEXEC=$(CARGO_HOME)/bin/rustup
CARGOEXEC=$(CARGO_HOME)/bin/cargo

LOGFILES=log

installtools: install_verilator install_morty install_rust install_bender install_fusesoc install_sv2v install_cascade_python install_yosys install_miniconda install_toolchain install_spike install_makeelf

install_verilator: | log
	( unset VERILATOR_ROOT && cd verilator && autoconf && ./configure --prefix=$(PREFIX_CASCADE) && make -j$(CASCADE_JOBS) && make install ) >$(LOGFILES)/verilator.log 2>&1

install_sv2v: $(PREFIX_CASCADE)/bin/stack | log
	( cd sv2v && make -j$(CASCADE_JOBS) && mkdir -p $(PREFIX_CASCADE)/bin/ && cp bin/sv2v $(PREFIX_CASCADE)/bin/ ) >$(LOGFILES)/sv2v.log 2>&1

$(PREFIX_CASCADE)/bin/stack: | log
	sh stack/gethaskellstack.sh -d $(PREFIX_CASCADE)/bin

install_yosys: | log
	( cd cascade-yosys && make config-gcc && make PREFIX=$(PREFIX_CASCADE) -j$(CASCADE_JOBS) && make PREFIX=$(PREFIX_CASCADE) install ) >$(LOGFILES)/yosys.log 2>&1

install_rust: $(RUSTEXEC)

install_cascade_python: $(CASCADE_PYTHON_VENV) | log
	(  \
		set -e; \
		$(CASCADE_PYTHON_VENV)/bin/pip install -r ../design-processing/python-requirements.txt; \
		$(CASCADE_PYTHON_VENV)/bin/pip install ninja==1.10.2 \
	)  >$(LOGFILES)/cascade-python.log 2>&1

$(RUSTEXEC): | log
	( CARGO_HOME=\$CARGO_HOME RUSTUP_HOME=\$RUSTUP_HOME curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y ) >$(LOGFILES)/rust.log 2>&1

install_morty: $(RUSTEXEC) | log
ifdef DO_INSTALL_OLD_VERSIONS
	$(CARGOEXEC) install --force --path morty --root $(PREFIX_CASCADE) >$(LOGFILES)/morty.log 2>&1
else
	$(CARGOEXEC) install --force morty --root $(PREFIX_CASCADE)
endif

install_bender: $(RUSTEXEC) | log
ifdef DO_INSTALL_OLD_VERSIONS
	$(CARGOEXEC) install --force --path bender --root $(PREFIX_CASCADE) >$(LOGFILES)/bender.log 2>&1
else
	$(CARGOEXEC) install --force bender --root $(PREFIX_CASCADE)
endif

install_fusesoc: $(CASCADE_PYTHON_VENV) | log
	$(CASCADE_PYTHON_VENV)/bin/pip install fusesoc >$(LOGFILES)/fusesoc.log 2>&1

install_miniconda: $(CASCADE_PYTHON_VENV) | log
	mkdir -p miniconda
	( wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda/miniconda.sh \
		&& cd miniconda/ && bash miniconda.sh -u -b -p $(PREFIX_CASCADE)/miniconda \
		&& $(PREFIX_CASCADE)/miniconda/bin/conda update -y -n base -c defaults conda \
		&& $(PREFIX_CASCADE)/miniconda/bin/conda config --add channels conda-forge \
		&& $(PREFIX_CASCADE)/miniconda/bin/conda config --set channel_priority strict \
		) >$(LOGFILES)/miniconda.log 2>&1

install_toolchain: $(PREFIX_CASCADE)/riscv | log
	# make also does install
	( cd riscv-gnu-toolchain/ && ./configure --prefix=$(PREFIX_CASCADE)/riscv --with-arch=rv32imc --with-cmodel=medlow --enable-multilib && make -j $(CASCADE_JOBS) ) >$(LOGFILES)/toolchain.log 2>&1

install_spike: $(PREFIX_CASCADE)/riscv | log
	(cd riscv-isa-sim && mkdir -p build && cd build && ../configure --prefix=$(PREFIX_CASCADE)/riscv && make -j $(CASCADE_JOBS) && make install) >$(LOGFILES)/spike.log 2>&1

install_makeelf: | log
	(cd makeelf && git checkout finercontrol && $(PYTHON) setup.py install) >$(LOGFILES)/makeelf.log 2>&1

$(CASCADE_PYTHON_VENV): | log
	$(PYTHON) -mvenv $(CASCADE_PYTHON_VENV)

cleantools:
	@echo "This is a fairly destructive recipe. Really know what's going to happen?"
	@echo "If so, press enter. Otherwise, press ^C."
	@echo -n "  >  "
	@read line
	set -x; for x in riscv-isa-sim bender morty riscv-gnu-toolchain sv2v verilator; do ( cd $$x && git clean -xfd ); done
	rm -rf $(PREFIX_CASCADE)
	rm -f $(LOGFILES)/*.log

$(PREFIX_CASCADE)/riscv log:
	mkdir -p $@
