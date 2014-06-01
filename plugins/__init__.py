from cement.core import handler, controller
from common import logger
import common
import requests

class BasePlugin(controller.CementBaseController):

    valid_enumerate = ['u', 'p', 't']
    class ScanningMethod():
        not_found = 404
        forbidden = 403
        ok = 200

    class Meta:
        label = 'baseplugin'
        stacked_on = 'base'

        arguments = []

    def enumerate_route(self):
        url, enumerate = self.app.pargs.url, self.app.pargs.enumerate
        method = self.app.pargs.method

        pbu = self.app.pargs.plugins_base_url
        plugins_base_url = pbu if pbu else self.plugins_base_url

        url = common.validate_url(url)
        common.validate_enumerate(enumerate, self.valid_enumerate)

        if method:
            scanning_method = common.validate_method(method, self.ScanningMethod)
        else:
            scanning_method = self.determine_scanning_method(url)

        functionality = {}
        if enumerate == "p":
            noun = "plugins"
            functionality[noun] = getattr(self, "enumerate_plugins")
        elif enumerate == "u":
            self.enumerate_users(url, scanning_method)
        elif enumerate == "t":
            self.enumerate_themes(url, scanning_method)

        common.echo(common.template("common/scan_begin.tpl", {"noun": noun, "url": url,
            "plugins_base_url": plugins_base_url, "scanning_method": scanning_method}))

        for enumerate in functionality:
            finds = functionality[enumerate](url, plugins_base_url, scanning_method)

            common.echo(common.template("common/list_noun.tpl", {"noun":noun,
                "items":finds, "empty":len(finds) == 0, "Noun":noun.capitalize()}))

        #finds = self.enumerate_plugins(url, plugins_base_url, scanning_method)


    def determine_scanning_method(self, url):
        folder_resp = requests.get(url + self.folder_url)
        ok_resp = requests.get(url + self.regular_file_url)

        logger.debug("determine_scanning_method: Server responded with %s and %s for urls %s and %s"
                % (folder_resp.status_code, ok_resp.status_code,
                    self.folder_url, self.regular_file_url))

        if folder_resp.status_code == 403 and ok_resp.status_code == 200:
            return self.ScanningMethod.forbidden
        if folder_resp.status_code == 404 and ok_resp.status_code == 200:
            logger.warning("Known %s folders have returned 404 Not Found. If modules do not have a %s file they will not be detected." %
                    (self._meta.label, self.module_readme_file))
            return self.ScanningMethod.not_found
        if folder_resp.status_code == 200 and ok_resp.status_code == 200:
            logger.warning("""Known folder names for %s are returning 200 OK. Is directory listing enabled?""" % self._meta.label)
            return self.ScanningMethod.ok
        else:
            raise RuntimeError("""It is possible that the website is not running %s. If you disagree, please specify a --method.""" %
                    self._meta.label)

    def enumerate_plugins(self, url, plugins_base_url, scanning_method):
        found_plugins = []

        if isinstance(plugins_base_url, basestring):
            base_urls = [plugins_base_url]
        else:
            base_urls = plugins_base_url

        for base_url in base_urls:
            plugins = self.plugins_get()

            if scanning_method == self.ScanningMethod.not_found:
                url_template = base_url + self.module_readme_file
                expected_status = 200
            else:
                url_template = base_url
                expected_status = scanning_method

            for plugin in plugins:
                r = requests.get(url_template % (url, plugin))
                if r.status_code == expected_status:
                    found_plugins.append(plugin)

        return found_plugins

    def enumerate_users(self, url):
        raise NotImplementedError("Not implemented yet.")

    def enumerate_themes(self, url):
        raise NotImplementedError("Not implemented yet.")
