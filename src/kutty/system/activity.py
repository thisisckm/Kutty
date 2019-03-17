import psutil

from ..activity import Activity


class SystemActivity(Activity):
    def __init__(self):
        Activity.__init__(self)
        self._first_deploy()

    def _pid_exists(self, pid, port_no):
        if psutil.pid_exists(pid):
            try:
                ps = psutil.Process(pid)
                cons = ps.connections()
                if cons and cons[0].laddr and str(cons[0].laddr[1]) == port_no:
                    return True
            except psutil.AccessDenied:
                return False
        return False

    def healtcheck(self):
        total_instances_count = self.odoo_instances.count()
        if total_instances_count == 0:
            return False
        unused_instances_count = self.odoo_instances.count({"status": {"$in": ["Stopped", "Stopping", "Deploying"]}})
        if total_instances_count == unused_instances_count:
            return False
        else:
            running_instances = self.odoo_instances.find({"status": "Running"})
            for instance in running_instances:
                if not self._pid_exists(int(instance['pid']), instance['port_no']):
                    return False

        return True


class SException(Exception):
    pass
