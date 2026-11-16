# Public APIs

### Social

API | Description | Auth | HTTPS | CORS |
|---|---|---|---|---|
| [4chan](https://github.com/4chan/4chan-API) | Image-based bulletin board | No | Yes | Yes |
| [API Direct](https://apidirect.io/docs#overview) | Real-time social media data | `apiKey` | Yes | Yes |
| [Ayrshare](https://www.ayrshare.com) | Social media management APIs | `apiKey` | Yes | Yes |
| [Blogger](https://example.com/blogger) | Ignored: not an assigned entry | `OAuth` | Yes | Unknown |

### Development

API | Description | Auth | HTTPS | CORS |
|---|---|---|---|---|
| [4chan](https://example.com/wrong-category) | Ignored: not the Social category | No | Yes | Yes |

```markdown
### Social
API | Description | Auth | HTTPS | CORS |
|---|---|---|---|---|
| [4chan](https://example.com/backtick-fenced) | Ignored: inside a backtick fence | No | Yes | Yes |
| [Fake API](https://example.com/fake) | Ignored: fake link in a backtick fence | No | Yes | Yes |
```

~~~markdown
### Social
API | Description | Auth | HTTPS | CORS |
|---|---|---|---|---|
| [Ayrshare](https://example.com/tilde-fenced) | Ignored: inside a tilde fence | `apiKey` | Yes | Yes |
| [API Direct](https://example.com/tilde-fenced-2) | Ignored: inside a tilde fence | No | Yes | Yes |
~~~

```markdown
### Social
API | Description | Auth | HTTPS | CORS |
|---|---|---|---|---|
| [4chan](https://example.com/inside-nested-fence) | Ignored: inside the original fence | No | Yes | Yes |
```python
### Social
API | Description | Auth | HTTPS | CORS |
|---|---|---|---|---|
| [Ayrshare](https://example.com/after-invalid-closing-fence) | Ignored: ```python is not a closing fence | `apiKey` | Yes | Yes |
```

````markdown
### Social
API | Description | Auth | HTTPS | CORS |
|---|---|---|---|---|
| [4chan](https://example.com/inside-short-close-fence) | Ignored: closing fence is shorter than the opener | No | Yes | Yes |
```
### Social
API | Description | Auth | HTTPS | CORS |
|---|---|---|---|---|
| [API Direct](https://example.com/after-short-close-fence) | Ignored: still inside the fence | No | Yes | Yes |
````

```markdown
### Social
API | Description | Auth | HTTPS | CORS |
|---|---|---|---|---|
| [4chan](https://example.com/inside-info-close-fence) | Ignored: closing fence has trailing text | No | Yes | Yes |
``` not-a-close
### Social
API | Description | Auth | HTTPS | CORS |
|---|---|---|---|---|
| [Ayrshare](https://example.com/after-info-close-fence) | Ignored: still inside the fence | `apiKey` | Yes | Yes |
```

```markdown
### Social
API | Description | Auth | HTTPS | CORS |
|---|---|---|---|---|
| [4chan](https://example.com/inside-wrong-marker-fence) | Ignored: a tilde fence cannot close a backtick fence | No | Yes | Yes |
~~~~
### Social
API | Description | Auth | HTTPS | CORS |
|---|---|---|---|---|
| [Ayrshare](https://example.com/after-wrong-marker-fence) | Ignored: still inside the fence | `apiKey` | Yes | Yes |
```
