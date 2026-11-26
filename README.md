# Kuo Jinn, portfolio

A one-page portfolio site. `index.html` is the whole site. The `assets` folder holds the images, and `src` holds the files it is built from.

## Live site

The site is served free by GitHub Pages at https://kuojinn.github.io from the `main` branch. Any change pushed to `main` goes live within a minute or two.

## Use your own domain (optional)

1. Buy a domain such as `kuojinn.com` from any registrar.
2. In **Settings → Pages → Custom domain**, enter the domain and click **Save**.
3. At your registrar, add the DNS records GitHub shows you. Then tick **Enforce HTTPS** once it becomes available.

## Making changes

Text, projects and contact details are all in `src/content.json`. After editing it, run `python3 src/build.py` to regenerate `index.html`. Or just ask Claude to make the change.

To use a short muted video loop behind a project on the index page instead of a still image, put the clip in `assets/<project>/` and ask Claude to wire it in.
