.. image:: https://raw.githubusercontent.com/quantumlib/Cirq/master/docs/_static/Cirq_logo_color.png
  :target: https://github.com/quantumlib/cirq
  :alt: Cirq
  :width: 500px

Cirq is a Python library for writing, manipulating, and optimizing quantum
circuits and running them against quantum computers and simulators.

.. image:: https://travis-ci.com/quantumlib/Cirq.svg?token=7FwHBHqoxBzvgH51kThw&branch=master
  :target: https://travis-ci.com/quantumlib/Cirq
  :alt: Build Status

.. image:: https://badge.fury.io/py/cirq.svg
    :target: https://badge.fury.io/py/cirq

.. image:: https://readthedocs.org/projects/cirq/badge/?version=latest
    :target: https://readthedocs.org/projects/cirq/versions/
    :alt: Documentation Status


Installation and Documentation
------------------------------

Cirq documentation is available at `cirq.readthedocs.io <https://cirq.readthedocs.io>`_.

Documentation for the latest **unstable** version of cirq (tracks the repository's master branch; what you get if you ``pip install cirq-unstable``), is available at `cirq.readthedocs.io/latest <https://cirq.readthedocs.io/en/latest/>`_.

Documentation for the latest **stable** version of cirq (what you get if you ``pip install cirq``) is available at `cirq.readthedocs.io/stable <https://cirq.readthedocs.io/en/stable/>`_.


- `Installation <https://cirq.readthedocs.io/en/stable/install.html>`_
- `Documentation <https://cirq.readthedocs.io>`_
- `Tutorial <https://cirq.readthedocs.io/en/stable/tutorial.html>`_

For the latest news regarding Cirq, sign up to the `Cirq-announce email list <https://groups.google.com/forum/#!forum/cirq-announce>`__!


Hello Qubit
-----------

A simple example to get you up and running:

.. code-block:: python

  import cirq

  # Pick a qubit.
  qubit = cirq.GridQubit(0, 0)

  # Create a circuit
  circuit = cirq.Circuit(
      cirq.X(qubit)**0.5,  # Square root of NOT.
      cirq.measure(qubit, key='m')  # Measurement.
  )
  print("Circuit:")
  print(circuit)

  # Simulate the circuit several times.
  simulator = cirq.Simulator()
  result = simulator.run(circuit, repetitions=20)
  print("Results:")
  print(result)

Example output:

.. code-block::

  Circuit:
  (0, 0): ───X^0.5───M('m')───
  Results:
  m=11000111111011001000


Feature requests / Bugs / Questions
-----------------------------------

If you have feature requests or you found a bug, please `file them on Github <https://github.com/quantumlib/Cirq/issues/new/choose>`__.

For questions about how to use Cirq post to
`Quantum Computing Stack Exchange <https://quantumcomputing.stackexchange.com/>`__ with the
`cirq <https://quantumcomputing.stackexchange.com/questions/tagged/cirq>`__ tag.


Cirq Contributors Community
---------------------------

We welcome contributions! Before opening your first PR, a good place to start is to read our
`guidelines <https://github.com/quantumlib/cirq/blob/master/CONTRIBUTING.md>`__.

We are dedicated to cultivating an open and inclusive community to build software for near term quantum computers.
Please read our `code of conduct <https://github.com/quantumlib/cirq/blob/master/CODE_OF_CONDUCT.md>`__ for the rules of engagement within our community.

For real time informal discussions about Cirq, join our `cirqdev <https://gitter.im/cirqdev>`__ Gitter channel, come hangout with us!

**Cirq Cynque** is our weekly meeting for contributors to discuss upcoming features, designs, issues, community and status of different efforts.
To get an invitation please join the `cirq-dev email list <https://groups.google.com/forum/#!forum/cirq-dev>`__ which also serves as yet another platform to discuss contributions and design ideas.


See Also
--------

For those interested in using quantum computers to solve problems in
chemistry and materials science, we encourage exploring
`OpenFermion <https://github.com/quantumlib/openfermion>`__ and
its sister library for compiling quantum simulation algorithms in Cirq,
`OpenFermion-Cirq <https://github.com/quantumlib/openfermion-cirq>`__.

For machine learning enthusiasts, `Tensorflow Quantum <https://github.com/tensorflow/quantum>`__ is a great project to check out!

For a powerful quantum circuit simulator that integrates well with Cirq, we recommend looking at `qsim <https://github.com/quantumlib/qsim>`__.

Finally, `ReCirq <https://github.com/quantumlib/ReCirq>`__ contains real world experiments using Cirq.


Alpha Disclaimer
----------------

**Cirq is currently in alpha.**
We may change or remove parts of Cirq's API when making new releases.
To be informed of deprecations and breaking changes, subscribe to the
`cirq-announce google group mailing list <https://groups.google.com/forum/#!forum/cirq-announce>`__.


Cirq is not an official Google product. Copyright 2019 The Cirq Developers
