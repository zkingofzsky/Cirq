# Style guidelines

As mentioned in [CONTRIBUTING.md](CONTRIBUTING.md) we use use [pylint](https://www.pylint.org/) 
to check for style violations.  Pylint attempts to enforce styles in 
[PEP 8](https://www.python.org/dev/peps/pep-0008/). To see which lint checks we enforce, see the 
[dev_tools/conf/.pylintrc](dev_tools/conf/.pylintrc) file.

Here we include some extra style guidelines.

### Import statements

We follow the [import standards](https://www.python.org/dev/peps/pep-0008/#imports) of PEP 8, 
with the following guidance.  

In Cirq's main implementation code (not testing code), we prefer importing the full module. This
aids in mocking during tests.  Thus we prefer
```python
from cirq import ops
qubit = ops.NamedQubit('a')
```
in contrast to
```python
from cirq.ops import NamedQubit
qubit = NamedQubit('a')
``` 
or (the one we would prefer, but doing this causes cyclic dependencies)
```python
import cirq
qubit = cirq.NamedQubit('a')
```
The one exception to this is for the typing code, where we prefer the direct import 
```python
from typing import List
```
This exception allows typing hints to be more compact. 

In tests, however, we prefer that we use Cirq as you would use cirq externally. For code
that is in the Cirq core framework this is
```python
import cirq
qubit = cirq.NamedQubit('a')
```
For Cirq code that is outside of the core and does not appear at the `cirq` module level, 
for example work in `contrib`, one should use the highest level possible for test code
```python
import cirq
from cirq import contrib
contrib.circuit_to_latex_using_qcircuit(cirq.Circuit())
``` 

Of course, if this import style fundamentally cannot be used, do not let this
block submitting a pull request for the code as we will definitely grant
exceptions.

#### Typing based import cycles

An import cycle is where modules need to import each other (perhaps indirectly).
Sometimes in order to add a type annotation you have to add an import which
causes a cycle. To avoid this we use the `TYPE_CHECKING` constant provided 
by `typing`:
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # pylint: disable=unused-import
    import module.that.causes.cycle
```
Note that if you do this you will need to use the string version of the type,
```python
def my_func() -> 'module.that.causes.cycle.MyClass':
    pass
```

#### Nomenclature

Using consistent wording across Cirq is important for lowering users
cognitive load. For rule governing naming, see the 
[nomenclature guidelines](docs/dev/nomenclature.md).
