# Expected usage

First lets make a distinction. Either the thing you work on is a package that is used in other projects at which point you should do

```python
import logging
logger = logging.getLogger(__name__)
```

wherever you want to do logging of any kind. You should do nothing else.

If you are working on a script, a service or something that is a final product, you should do

```python
import atro_core.logging
< NEED TO FINISH HERE > 
```
