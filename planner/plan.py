import utils
import subprocess



class Plan():
    def __init__(self,model, encoder):
        self.plan = self.extractPlan(model, encoder)

    def extractPlan(self, model, encoder):
        """
        Extract linear plan from model of the formula
        """

        ## extract plan for model

        return plan


    def validate(self, val, domain, problem):
        from tempfile import NamedTemporaryFile

        print('Validating plan...')

        plan_to_str = '\n'.join('{}: {}'.format(key, val) for key, val in self.plan.items())

        with NamedTemporaryFile(mode='w+') as temp:

            temp.write(plan_to_str)
            temp.seek(0)

            try:
                output = subprocess.check_output([val, domain, problem, temp.name])

            except subprocess.CalledProcessError as e:

                print('Unknown error, exiting now...')
                sys.exit()

        temp.close()

        if 'Plan valid' in output:
            return plan_to_str
        else:
            return None


    def pprint(self, dest):
        print('Printing plan to {}'.format(dest))